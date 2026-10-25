#!/usr/bin/env python3
"""List the URLs of an existing website, so none are lost when the new site replaces it.

  python3 old-urls.py https://www.oldsite.com > old-urls.txt

Reads sitemap.xml (including sitemap indexes) and also follows links from the
home page and the pages it links to (same host, two levels). Prints one path
per line, sorted. Run it BEFORE the domain points at the new site.
"""
import html
import re
import sys
from collections import defaultdict
from urllib.parse import quote, unquote
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = {"User-Agent": "Mozilla/5.0 (site-migration-check)"}


def get(url, limit=3_000_000):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            ctype = r.headers.get("Content-Type", "")
            return r.geturl(), ctype, r.read(limit).decode("utf-8", "replace")
    except Exception:
        return None, "", ""


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    base = sys.argv[1].rstrip("/")
    final, _, _ = get(base + "/")
    host = urlparse(final or base).netloc.lower().removeprefix("www.")
    paths = set()

    action = re.compile(r"(cart|basket|checkout|login|logout|signin|account|session|sid=|add-to|addto|wishlist|print=|share=|replytocom)", re.I)

    def keep(u):
        u = html.unescape(html.unescape(u.strip()))
        if re.search(r"\s", u.strip()) and "%20" not in u:
            u = u.strip()
        p = urlparse(u)
        if p.netloc.lower().removeprefix("www.") != host:
            return None
        if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|css|js|ico|woff2?|mp4|zip|pdf)$", p.path, re.I):
            return None
        if action.search(p.path + "?" + p.query) or p.path.endswith("&amp") or "&amp;" in p.path:
            return None
        path = quote(unquote(p.path or "/"), safe="/-._~!$&'()*+,;=:@%")
        return path + (("?" + p.query) if p.query else "")

    # Sitemaps
    todo, seen = [base + "/sitemap.xml", base + "/sitemap_index.xml", base + "/wp-sitemap.xml"], set()
    while todo:
        sm = todo.pop()
        if sm in seen or len(seen) > 50:
            continue
        seen.add(sm)
        _, _, body = get(sm)
        for loc in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", body):
            if loc.endswith(".xml") or "sitemap" in loc.rsplit("/", 1)[-1]:
                todo.append(loc)
            elif keep(loc):
                paths.add(keep(loc))

    # Crawl two levels from the home page
    frontier, visited = [final or base + "/"], set()
    for _depth in range(2):
        nxt = []
        for page in frontier[:150]:
            if page in visited:
                continue
            visited.add(page)
            url, ctype, body = get(page)
            if not url or "html" not in ctype:
                continue
            k = keep(url)
            if k:
                paths.add(k)
            parser = Links()
            try:
                parser.feed(body)
            except Exception:
                pass
            for href in parser.links:
                if href.startswith(("mailto:", "tel:", "#", "javascript:")):
                    continue
                absu = urljoin(url, href.split("#")[0])
                k = keep(absu)
                if k:
                    paths.add(k)
                    nxt.append(absu)
        frontier = nxt
    # Collapse big numbered families (/design-123/..., /product/4567) into one line each.
    families = defaultdict(list)
    for p in paths:
        path = p.split("?")[0]
        segs = [x for x in path.split("/") if x]
        if len(segs) >= 2 and re.search(r"\d", segs[0]):
            key = "/" + re.sub(r"\d+", "N", segs[0]) + "/*"
        else:
            key = re.sub(r"\d+", "N", path)
        families[key].append(p)
    shown = 0
    for pattern, members in sorted(families.items()):
        members.sort()
        if len(members) > 15:
            print(f"# {len(members)} URLs like {pattern} (one wildcard rule can cover them); examples:")
            for m in members[:3]:
                print(m)
            shown += 3
        else:
            for m in members:
                print(m)
            shown += len(members)
    print(f"# {len(paths)} paths from {host}, {shown} listed", file=sys.stderr)


if __name__ == "__main__":
    main()
