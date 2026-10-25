#!/usr/bin/env python3
"""Domain checks for moving a website to Cloudflare, with only the Python stdlib.

  python3 dnscheck.py audit <domain>             registrar, nameservers, DNSSEC, and every
                                                 record that matters (web, email, verification);
                                                 saves dns-audit-<domain>.json
  python3 dnscheck.py compare <domain> <ns-host> asks a specific nameserver (e.g. the one
                                                 Cloudflare assigned) for everything in the audit
                                                 and lists what is missing or different
  python3 dnscheck.py status <domain>            nameservers now, DNSSEC, and HTTPS on the bare
                                                 domain and www (status, redirect, certificate)
  python3 dnscheck.py cf-records <domain> [--skip-web]
                                                 the audited records as Cloudflare API bodies (JSON),
                                                 ready to create in the new zone; --skip-web leaves
                                                 out the bare-domain and www website records
  python3 dnscheck.py available <name.tld> ...   quick registration check through RDAP / WHOIS

Give the main domain (example.co.uk); a leading www. is dropped. Accented domains are
converted to their xn-- form.

Exit code 1 from compare means records differ; fix them before changing nameservers.
"""
import json
import os
import random
import socket
import ssl
import struct
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

TYPES = {"A": 1, "NS": 2, "CNAME": 5, "SOA": 6, "PTR": 12, "MX": 15, "TXT": 16, "AAAA": 28,
         "SRV": 33, "DS": 43, "CAA": 257}
TYPE_NAMES = {v: k for k, v in TYPES.items()}
PUBLIC_RESOLVERS = ["1.1.1.1", "8.8.8.8"]
DKIM_SELECTORS = ["google", "selector1", "selector2", "default", "k1", "k2", "k3", "s1", "s2",
                  "mail", "dkim", "fm1", "fm2", "fm3", "protonmail", "protonmail2", "protonmail3",
                  "zoho", "zmail", "resend", "mandrill", "hs1", "hs2", "smtp", "mxvault",
                  "privateemail", "sig1", "everlytickey1", "everlytickey2", "cm", "pm", "ionos",
                  "titan1", "titan2", "brevo1", "brevo2", "mailjet", "sendgrid", "s1024"]
SUBDOMAINS = ["www", "mail", "webmail", "email", "smtp", "imap", "pop", "autodiscover",
              "autoconfig", "lyncdiscover", "sip", "enterpriseregistration",
              "enterpriseenrollment", "shop", "store", "blog", "app", "portal", "booking",
              "book", "ftp", "cpanel", "calendar", "docs", "em", "links", "click", "track"]
SRV_NAMES = ["_autodiscover._tcp", "_sip._tls", "_sipfederationtls._tcp", "_imaps._tcp",
             "_submission._tcp"]
UA = {"User-Agent": "website-domain-check/1.0", "Accept": "application/json"}


# ---------------------------------------------------------------- DNS wire format
def _encode_name(name):
    out = b""
    for label in name.rstrip(".").split("."):
        if label:
            out += bytes([len(label)]) + label.encode("idna")
    return out + b"\x00"


def _read_name(msg, off):
    labels, jumped, end = [], False, off
    for _ in range(128):
        length = msg[off]
        if length & 0xC0 == 0xC0:
            if not jumped:
                end = off + 2
            off = ((length & 0x3F) << 8) | msg[off + 1]
            jumped = True
            continue
        if length == 0:
            if not jumped:
                end = off + 1
            break
        labels.append(msg[off + 1:off + 1 + length].decode("latin-1"))
        off += 1 + length
    return ".".join(labels), end


def _parse_rdata(msg, rtype, off, rdlen):
    rd = msg[off:off + rdlen]
    if rtype == 1:
        return socket.inet_ntop(socket.AF_INET, rd)
    if rtype == 28:
        return socket.inet_ntop(socket.AF_INET6, rd)
    if rtype in (2, 5, 12):
        return _read_name(msg, off)[0].lower() + "."
    if rtype == 15:
        pref = struct.unpack("!H", rd[:2])[0]
        return f"{pref} {_read_name(msg, off + 2)[0].lower()}."
    if rtype == 16:
        parts, i = [], 0
        while i < len(rd):
            n = rd[i]
            parts.append(rd[i + 1:i + 1 + n].decode("utf-8", "replace"))
            i += 1 + n
        return "".join(parts)
    if rtype == 33:
        pri, weight, port = struct.unpack("!HHH", rd[:6])
        return f"{pri} {weight} {port} {_read_name(msg, off + 6)[0].lower()}."
    if rtype == 43:
        tag, alg, dtype = struct.unpack("!HBB", rd[:4])
        return f"{tag} {alg} {dtype} {rd[4:].hex()}"
    if rtype == 257:
        flags, tlen = rd[0], rd[1]
        return f'{flags} {rd[2:2 + tlen].decode()} "{rd[2 + tlen:].decode()}"'
    if rtype == 6:
        mname, o = _read_name(msg, off)
        rname, o = _read_name(msg, o)
        return f"{mname}. {rname}."
    return rd.hex()


def _query_wire(name, rtype, server, timeout=3.0):
    qid = random.randint(0, 65535)
    flags = 0x0100  # recursion desired (ignored by authoritative servers)
    packet = struct.pack("!HHHHHH", qid, flags, 1, 0, 0, 0) + _encode_name(name) + struct.pack("!HH", TYPES[rtype], 1)
    msg = None
    for _ in range(2):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(timeout)
                s.sendto(packet, (server, 53))
                msg, _ = s.recvfrom(4096)
            break
        except (socket.timeout, OSError):
            msg = None
    if msg is None or (struct.unpack("!H", msg[2:4])[0] & 0x0200):  # no answer or truncated
        with socket.create_connection((server, 53), timeout=timeout + 2) as s:
            s.sendall(struct.pack("!H", len(packet)) + packet)
            ln = struct.unpack("!H", _recv_exact(s, 2))[0]
            msg = _recv_exact(s, ln)
    rcode = struct.unpack("!H", msg[2:4])[0] & 0x000F
    qd, an = struct.unpack("!HH", msg[4:8])
    off = 12
    for _ in range(qd):
        off = _read_name(msg, off)[1] + 4
    answers = []
    for _ in range(an):
        rname, off = _read_name(msg, off)
        t, _cls, _ttl, rdlen = struct.unpack("!HHIH", msg[off:off + 10])
        off += 10
        answers.append((rname.lower(), TYPE_NAMES.get(t, str(t)), _parse_rdata(msg, t, off, rdlen)))
        off += rdlen
    return rcode, answers


def _recv_exact(s, n):
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise OSError("connection closed")
        buf += chunk
    return buf


def _query_doh(name, rtype):
    url = f"https://cloudflare-dns.com/dns-query?name={name}&type={rtype}"
    req = urllib.request.Request(url, headers={"accept": "application/dns-json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.load(r)
    out = []
    for a in d.get("Answer", []):
        t = TYPE_NAMES.get(a["type"], str(a["type"]))
        data = a["data"]
        if t == "TXT":
            data = "".join(p for p in data.split('"') if p.strip() and p != " ") if data.startswith('"') else data
        if t in ("CNAME", "NS", "MX", "SRV") and not data.endswith("."):
            data += "."
        out.append((a["name"].rstrip(".").lower(), t, data.lower() if t in ("CNAME", "NS", "MX", "SRV") else data))
    return d.get("Status", 0), out


_UDP_OK = None


def lookup(name, rtype, server=None):
    """Return the record values of exactly this name and type (CNAME chains excluded)."""
    global _UDP_OK
    name = name.rstrip(".").lower()
    if server is None and _UDP_OK is False:
        _, ans = _query_doh(name, rtype)
    else:
        try:
            _, ans = _query_wire(name, rtype, server or PUBLIC_RESOLVERS[0])
            if server is None:
                _UDP_OK = True
        except (OSError, struct.error, IndexError):
            if server is not None:
                raise
            _UDP_OK = False
            _, ans = _query_doh(name, rtype)
    return sorted({v for (n, t, v) in ans if t == rtype and n.rstrip(".") == name})


def resolve_host(host):
    return socket.getaddrinfo(host, 53, socket.AF_INET, socket.SOCK_DGRAM)[0][4][0]


# ---------------------------------------------------------------- RDAP
def rdap(domain):
    try:
        req = urllib.request.Request(f"https://rdap.org/domain/{domain}", headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        return {"http": e.code}
    except Exception as e:  # noqa: BLE001 - report and carry on
        return {"error": str(e)}
    registrar = None
    for ent in d.get("entities", []):
        if "registrar" in ent.get("roles", []):
            for v in (ent.get("vcardArray") or [None, []])[1]:
                if v[0] == "fn":
                    registrar = v[3]
    events = {e.get("eventAction"): e.get("eventDate") for e in d.get("events", [])}
    return {
        "http": 200,
        "registrar": registrar,
        "nameservers": sorted(n.get("ldhName", "").lower() for n in d.get("nameservers", [])),
        "dnssec_signed": d.get("secureDNS", {}).get("delegationSigned"),
        "expires": events.get("expiration"),
        "status": d.get("status", []),
    }


def _whois(domain):
    """Raw WHOIS over port 43 (no whois binary needed), for TLDs without RDAP."""
    def ask(server, q):
        with socket.create_connection((server, 43), timeout=10) as s:
            s.sendall((q + "\r\n").encode())
            buf = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
        return buf.decode("utf-8", "replace")
    try:
        tld = domain.rsplit(".", 1)[-1]
        server = next((l.split(":", 1)[1].strip() for l in ask("whois.iana.org", tld).splitlines()
                       if l.lower().startswith("whois:")), None)
        if not server:
            return {"error": "no whois server"}
        text = ask(server, domain)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    out = {"http": 200, "registrar": None, "expires": None, "nameservers": [], "status": [], "source": "whois"}
    for line in text.splitlines():
        k, _, v = line.strip().partition(":")
        k, v = k.strip().lower(), v.strip()
        if k in ("registrar", "sponsoring registrar") and v and not out["registrar"]:
            out["registrar"] = v
        elif k in ("registry expiry date", "expiry date", "expiration date", "paid-till", "renewal date") and v and not out["expires"]:
            out["expires"] = v
        elif k in ("name server", "nserver") and v:
            out["nameservers"].append(v.lower())
        elif k == "domain status" and v:
            out["status"].append(v.split()[0])
    low = text.lower()
    if "status: connect" in low or "status: active" in low or "status: registered" in low:
        out["registered"] = True
    free_words = ("status: free", "no match", "no entries found", "not been registered", "no data found",
                  "available for registration", "is free", "domain not found", "not registered")
    if any(w in low for w in free_words) or "not found" in low[:400]:
        out["http"] = 404
    return out


def registration(domain):
    """RDAP first; raw WHOIS when RDAP has no answer (some TLDs, e.g. .co, have no RDAP at rdap.org)."""
    info = rdap(domain)
    if info.get("http") == 200:
        return info
    w = _whois(domain)
    if w.get("registrar") or w.get("registered") or w.get("http") == 404:
        return w
    return {"http": None, "error": "no RDAP or WHOIS answer"}


def _wildcards(domain):
    """Answers a made-up subdomain gets; records equal to these are the wildcard, not real."""
    probe = f"zz-{random.randint(10**6, 10**7)}-nope.{domain}"
    return {t: lookup(probe, t) for t in ("CNAME", "A", "AAAA", "TXT")}


# ---------------------------------------------------------------- commands
def _clean(domain):
    d = domain.lower().strip().rstrip(".")
    d = d.split("://", 1)[-1].split("/", 1)[0]
    if d.startswith("www."):
        d = d[4:]
    try:
        d.encode("ascii")
    except UnicodeEncodeError:
        d = d.encode("idna").decode("ascii")
    return d


def audit(domain):
    domain = _clean(domain)
    info = registration(domain)
    print(f"Domain: {domain}")
    if info.get("http") == 200:
        print(f"Registrar: {info['registrar'] or 'unknown (ask the owner who they pay for the domain)'}")
        print(f"Expires: {info.get('expires') or 'unknown'}")
        locked = [s for s in info.get("status", []) if "prohibited" in s]
        if locked:
            print(f"Registry locks: {', '.join(locked)} (normal; only 'client update prohibited' blocks nameserver changes)")
    else:
        print(f"Registrar: RDAP lookup failed ({info}); ask the owner which company they renew the domain with")
    records = {}
    wild = _wildcards(domain)
    if any(wild.values()):
        print(f"Wildcard DNS: any made-up subdomain answers {[v for vs in wild.values() for v in vs]}; copy the * record too")

    def grab(name, rtype):
        vals = lookup(name, rtype)
        if vals and name != domain and wild.get(rtype) and vals == wild[rtype]:
            records.setdefault(f"*.{domain}", {})[rtype] = vals
            return []
        if vals:
            records.setdefault(name, {})[rtype] = vals
        return vals

    ns = grab(domain, "NS")
    ds = grab(domain, "DS")
    print(f"Nameservers now: {', '.join(ns) or 'none found'}")
    if not ns:
        print("WARNING: no nameservers found. Check the spelling, and give the main domain (example.co.uk), not a subdomain.")
    print(f"DNSSEC: {'ON - must be switched off at the registrar before changing nameservers' if ds else 'off'}")
    for t in ("A", "AAAA", "MX", "TXT", "CAA"):
        grab(domain, t)
    grab(f"_dmarc.{domain}", "TXT")
    for sel in DKIM_SELECTORS:
        for t in ("TXT", "CNAME"):
            grab(f"{sel}._domainkey.{domain}", t)
    for sub in SUBDOMAINS:
        n = f"{sub}.{domain}"
        if not grab(n, "CNAME"):
            grab(n, "A")
            grab(n, "AAAA")
    for srv in SRV_NAMES:
        grab(f"{srv}.{domain}", "SRV")

    # Hosts inside this domain that other records point at (mx1.example.com,
    # a CNAME to smtp2.example.com...). Not on any fixed list, so look them up.
    def targets():
        out = set()
        for by_type in list(records.values()):
            for t, vals in by_type.items():
                for v in vals:
                    if t in ("MX", "SRV", "CNAME"):
                        host = v.split()[-1].rstrip(".").lower()
                        if host.endswith("." + domain) and host not in records:
                            out.add(host)
        return out
    for _ in range(2):
        for host in targets():
            if not grab(host, "CNAME"):
                grab(host, "A")
                grab(host, "AAAA")

    print("\nRecords found (copy every one of these to Cloudflare before switching):")
    for name in sorted(records, key=lambda n: (n != domain, n)):
        for t, vals in records[name].items():
            if t in ("NS", "DS"):
                continue
            for v in vals:
                print(f"  {name:45} {t:6} {v}")
    mx = records.get(domain, {}).get("MX", [])
    if mx and all(v.split()[-1] in (".", "") for v in mx):
        email = "none (null MX: this domain is set to receive no mail)"
    else:
        email = "none (no MX records)" if not mx else _email_provider(mx)
    print(f"\nEmail: {email}")
    web_hosts = {domain, f"www.{domain}"}
    mailish = ("mail", "smtp", "imap", "pop", "webmail", "autodiscover", "autoconfig", "email", "mx", "_")
    pointing = [(n, t, v) for n, by in records.items() for t, vals in by.items() for v in vals
                if t in ("MX", "CNAME", "SRV") and v.split()[-1].rstrip(".").lower() in web_hosts]
    mail_on_web = [f"{n} {t} {v}" for n, t, v in pointing
                   if t in ("MX", "SRV") or n.split(".")[0].startswith(mailish)]
    others = [f"{n} {t} {v}" for n, t, v in pointing
              if f"{n} {t} {v}" not in mail_on_web and n != f"www.{domain}"]
    spf = [v for v in records.get(domain, {}).get("TXT", []) if v.lower().startswith("v=spf1")]
    spf_web = [v for v in spf if any(m in v.lower().split() for m in ("a", "+a", "mx", "+mx"))]
    if mail_on_web or spf_web:
        print("MAIL ON THE WEBSITE ADDRESS: these depend on the bare domain or www, which change at launch:")
        for line in mail_on_web + [f"{domain} TXT {v}" for v in spf_web]:
            print(f"  {line}")
        print("  Before launch: give mail its own host (mail.<domain> A <current web IP>, DNS only), point the")
        print("  MX/CNAMEs at it, and replace SPF 'a'/'mx' with ip4:<that IP>. See 'Mail on the website address' in SKILL.md.")
    if others:
        print("OTHER NAMES THAT FOLLOW THE WEBSITE ADDRESS (they will show the new site, or an error, after launch):")
        for line in others:
            print(f"  {line}")
        print("  Ask the owner what each is for. Usually: point it at its real service, or delete it if unused.")
    web = records.get(domain, {}).get("A", []) + records.get(f"www.{domain}", {}).get("CNAME", [])
    print(f"Current website points to: {', '.join(web) or 'nothing'}")
    web_ips = set(records.get(domain, {}).get("A", []))
    mail_ips = set()
    for v in mx:
        host = v.split()[-1].rstrip(".")
        if host:
            mail_ips.update(records.get(host, {}).get("A", []) or lookup(host, "A"))
    shared = web_ips & mail_ips
    if shared:
        ip = sorted(shared)[0]
        try:
            ptr = lookup(".".join(reversed(ip.split("."))) + ".in-addr.arpa", "PTR")
        except Exception:  # noqa: BLE001
            ptr = []
        print(f"MAIL ON THE OLD WEBSITE'S SERVER: mail and the website share {ip}" + (f" ({ptr[0].rstrip('.')})" if ptr else "") + ".")
        print("  Launch keeps mail working (its records are copied), but the owner must NOT cancel that hosting")
        print("  plan until their mailboxes have moved somewhere else.")
    print("\nNot visible to any lookup: records at unusual names (custom DKIM selectors, odd subdomains).")
    print("Ask for a zone export from the current DNS host, or compare Cloudflare's imported list with the host's DNS page.")
    out = {"domain": domain, "rdap": info, "records": records,
           "mail_on_web_address": bool(mail_on_web or spf_web),
           "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path = f"dns-audit-{domain}.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"Saved {os.path.abspath(path)}")


def _email_provider(mx):
    joined = " ".join(mx)
    for key, label in [("google", "Google Workspace"), ("outlook", "Microsoft 365"), ("mx.microsoft", "Microsoft 365"),
                       ("zoho", "Zoho Mail"), ("protonmail", "Proton Mail"), ("privateemail", "Namecheap Private Email"),
                       ("secureserver", "GoDaddy email"), ("ionos", "IONOS email"), ("hostinger", "Hostinger email"),
                       ("one.com", "one.com email"), ("titan", "Titan email"), ("mimecast", "Mimecast"),
                       ("cloudflare", "Cloudflare Email Routing"), ("messagingengine", "Fastmail")]:
        if key in joined:
            return f"{label} ({', '.join(mx)})"
    return ", ".join(mx)


def _norm(t, v):
    return v.rstrip(".").lower() if t in ("CNAME", "NS", "MX", "SRV") else v


def compare(domain, ns_host):
    domain = _clean(domain)
    path = f"dns-audit-{domain}.json"
    if not os.path.exists(path):
        print(f"No {path} here; run `audit {domain}` first, in this folder.")
        sys.exit(2)
    audit_data = json.load(open(path))
    server = resolve_host(ns_host)
    problems, ok = 0, 0
    print(f"Comparing live records with {ns_host} ({server}):")
    for name, by_type in audit_data["records"].items():
        for t, vals in by_type.items():
            if t in ("NS", "DS"):
                continue
            try:
                got = lookup(name, t, server)
            except Exception as e:  # noqa: BLE001
                print(f"  ?? {name} {t}: could not ask {ns_host} ({e})")
                problems += 1
                continue
            want = sorted(_norm(t, v) for v in vals)
            have = sorted(_norm(t, v) for v in got)
            # Proxied web records answer with Cloudflare IPs; that's expected for the site itself.
            if t in ("A", "AAAA") and have and name in (domain, f"www.{domain}"):
                ok += 1
                continue
            if t == "CNAME" and not have and name in (f"www.{domain}",):
                if lookup(name, "A", server) or lookup(name, "AAAA", server):
                    ok += 1
                    continue
            if want == have:
                ok += 1
            else:
                problems += 1
                missing = [v for v in want if v not in have]
                extra = [v for v in have if v not in want]
                print(f"  MISSING/DIFFERENT {name} {t}: need {missing or want}" + (f"; Cloudflare has {extra}" if extra else ""))
    print(f"{ok} matching, {problems} to fix.")
    if problems:
        print("Add the missing records in Cloudflare (DNS only / grey cloud for anything email-related), then run compare again.")
    sys.exit(1 if problems else 0)


def _https(host):
    result = {"host": host}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
        issuer = dict(x[0] for x in cert.get("issuer", []))
        result["certificate"] = f"valid, issued by {issuer.get('organizationName', '?')}, expires {cert.get('notAfter')}"
    except ssl.SSLCertVerificationError as e:
        result["certificate"] = f"NOT VALID ({e.verify_message})"
    except Exception as e:  # noqa: BLE001
        result["certificate"] = f"no HTTPS answer ({e.__class__.__name__}: {e})"
        return result

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    try:
        r = opener.open(urllib.request.Request(f"https://{host}/", headers=UA), timeout=15)
        body = r.read(200000).decode("utf-8", "replace")
        result["http"] = r.status
        import re
        m = re.search(r'<meta name="build" content="([^"]*)"', body)
        t = re.search(r"<title>(.*?)</title>", body, re.S)
        result["build"] = m.group(1) if m else None
        result["title"] = t.group(1).strip() if t else None
    except urllib.error.HTTPError as e:
        result["http"] = e.code
        result["redirect"] = e.headers.get("Location")
    except Exception as e:  # noqa: BLE001
        result["http"] = f"error {e}"
    return result


def status(domain):
    domain = _clean(domain)
    ns = lookup(domain, "NS")
    on_cf = bool(ns) and all(n.rstrip(".").endswith(".ns.cloudflare.com") for n in ns)
    print(f"Nameservers now: {', '.join(ns) or 'none'}{'  (Cloudflare)' if on_cf else ''}")
    print(f"DNSSEC (DS at registry): {'ON' if lookup(domain, 'DS') else 'off'}")
    for host in (domain, f"www.{domain}"):
        r = _https(host)
        line = f"https://{host}: certificate {r.get('certificate')}; HTTP {r.get('http', '-')}"
        if r.get("redirect"):
            line += f" -> {r['redirect']}"
        if r.get("title"):
            line += f"; title '{r['title'][:60]}'"
        if r.get("build"):
            line += f"; build {r['build'][:7]}"
        print(line)


def available(names):
    for n in names:
        n = _clean(n)
        info = registration(n)
        if lookup(n, "NS") or info.get("registered"):
            print(f"{n}: taken" + (f" (registrar {info['registrar']})" if info.get("registrar") else ""))
        elif info.get("http") == 404:
            print(f"{n}: not registered (probably available; confirm in the registrar's search)")
        elif info.get("http") is None:
            print(f"{n}: no registry answer and no DNS (probably available, unconfirmed; check in the registrar's search)")
        elif info.get("http") == 200:
            print(f"{n}: taken (registrar {info.get('registrar') or '?'}, expires {info.get('expires') or '?'})")
        else:
            print(f"{n}: unknown ({info}); check in the registrar's search")


def cf_records(domain, skip_web=False):
    """Turn dns-audit-<domain>.json into Cloudflare POST /dns_records bodies."""
    domain = _clean(domain)
    path = f"dns-audit-{domain}.json"
    if not os.path.exists(path):
        print(f"No {path} here; run `audit {domain}` first, in this folder.", file=sys.stderr)
        sys.exit(2)
    data = json.load(open(path))
    out = []
    for name, by_type in data["records"].items():
        web = name in (domain, f"www.{domain}")
        for t, vals in by_type.items():
            if t in ("NS", "DS", "SOA"):
                continue
            if skip_web and web and t in ("A", "AAAA", "CNAME"):
                continue
            for v in vals:
                body = {"type": t, "name": name, "ttl": 1}
                if t in ("A", "AAAA", "CNAME"):
                    body["content"] = v.rstrip(".")
                    # Everything starts as DNS only, exactly as it behaves today.
                    body["proxied"] = False
                elif t == "MX":
                    pri, host = v.split(" ", 1)
                    body.update(priority=int(pri), content=host.rstrip("."))
                elif t == "TXT":
                    body["content"] = '"' + v.replace('"', '\\"') + '"' if len(v) <= 255 else v
                elif t == "SRV":
                    pri, weight, port, target = v.split(" ")
                    body["data"] = {"priority": int(pri), "weight": int(weight), "port": int(port), "target": target.rstrip(".")}
                elif t == "CAA":
                    flags, tag, value = v.split(" ", 2)
                    body["data"] = {"flags": int(flags), "tag": tag, "value": value.strip('"')}
                else:
                    continue
                out.append(body)
    print(json.dumps(out, indent=1))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "audit":
        audit(args[0])
    elif cmd == "compare" and len(args) == 2:
        compare(args[0], args[1])
    elif cmd == "status":
        status(args[0])
    elif cmd == "cf-records":
        cf_records(args[0], skip_web="--skip-web" in args)
    elif cmd == "available":
        available(args)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
