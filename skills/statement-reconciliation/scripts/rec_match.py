#!/usr/bin/env python3
"""Match a statement to a ledger register one-to-one and compute both adjusted balances.

Python 3 standard library only. Reads CSV/JSON, writes result files to --out.
Never edits an input, never produces a balancing entry, never writes to a ledger.

    cd ~/skills/statement-reconciliation && python3 scripts/rec_match.py \
        --statement /home/user/in/statement.csv \
        --ledger /home/user/in/ledger.csv \
        --balances /home/user/in/balances.json \
        [--carried /home/user/in/carried.csv] \
        [--classify /home/user/in/classify.csv] \
        [--next-statement /home/user/in/next-statement.csv] \
        --out /home/user/out/rec/<account>-<YYYY-MM>

    python3 scripts/rec_match.py --selftest      # runs examples/scenarios/*

Input schemas are in references/input-schema.md. Exit codes:
  0  finished (read summary.json "status": RECONCILED or NOT RECONCILED)
  2  bad input: the message says what to fix
  3  STOPPED: a control failed (opening does not tie to the prior approved
     closing, or an input does not prove to its own closing balance)
"""

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import tempfile
from decimal import Decimal, InvalidOperation

# Default matching window in days for timing passes.
# default — confirm with the owner (printed in every summary).
DEFAULT_WINDOW_DAYS = 3
# Largest group a batch match may combine. Beyond this, leave it for a person.
MAX_BATCH = 6

STATEMENT_CLASSES = {"investigate", "correction", "bank-error", "ledger-error", "match"}
LEDGER_CLASSES = {"timing", "correction", "investigate"}


# Masking, same shape as bookkeeping-exception-escalation/scripts/build_pack.py:
# 6+ digits (optionally grouped by spaces or dashes) keep only their last 4;
# IBANs keep country and last 4; sort codes are starred; dates and amounts stay.
# Applied to every description and reference this script or write_workpaper.py
# writes, so no output (and no approved workpaper) holds a full account, card,
# mandate or trace number. The raw text stays only in the sandbox input.
IBAN = re.compile(r"\b([A-Z]{2})\d{2}[A-Z0-9 ]{11,30}?(\d{4})\b")
SORT_CODE = re.compile(r"\b\d{2}-\d{2}-\d{2}\b")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
LONG_DIGITS = re.compile(r"(?<![\d.])(?<!\d,)\d(?:[ -]?\d){5,}(?!\d)(?![.,]\d)")
PERIOD_RX = re.compile(r"(?<!\d)(?:19|20)\d{2}-\d{2}(?!\d)")


def mask(text):
    if not text:
        return text
    keep = {}

    def hold(m):
        key = f"\x00{len(keep)}\x00"
        keep[key] = m.group(0)
        return key

    t = ISO_DATE.sub(hold, str(text))
    t = PERIOD_RX.sub(hold, t)
    t = IBAN.sub(lambda m: f"{m.group(1)}** **** {m.group(2)}", t)
    t = SORT_CODE.sub("**-**-**", t)
    t = LONG_DIGITS.sub(lambda m: "****" + re.sub(r"\D", "", m.group(0))[-4:], t)
    for k, v in keep.items():
        t = t.replace(k, v)
    return t


class InputError(Exception):
    pass


class StopControl(Exception):
    pass


# ---------------------------------------------------------------- parsing

def money(value, where, q):
    text = str(value).strip().replace(",", "")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    try:
        return Decimal(text).quantize(q)
    except InvalidOperation:
        raise InputError(f"{where}: '{value}' is not a number. Use plain decimals like -12.50.")


def day(value, where):
    try:
        return dt.date.fromisoformat(str(value).strip())
    except ValueError:
        raise InputError(f"{where}: date '{value}' is not YYYY-MM-DD. Convert dates before matching.")


def norm(text):
    return re.sub(r"[^A-Z0-9]", "", str(text or "").upper())


def read_rows(path, side, q, need=("id", "date", "amount")):
    if not path:
        return []
    if not os.path.isfile(path):
        raise InputError(f"{side}: file not found: {path}")
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = {c.strip().lower(): c for c in (reader.fieldnames or [])}
        missing = [c for c in need if c not in cols]
        if missing:
            raise InputError(
                f"{side}: missing column(s) {missing}. Found {list(cols)}. "
                "See references/input-schema.md for the canonical columns."
            )
        rows, seen = [], set()
        for n, raw in enumerate(reader, start=2):
            r = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            where = f"{os.path.basename(path)} line {n}"
            if not r.get("id"):
                raise InputError(f"{where}: empty id. Every row needs a unique id (line number is fine).")
            if r["id"] in seen:
                raise InputError(f"{where}: id '{r['id']}' appears twice in {side}. Ids must be unique.")
            seen.add(r["id"])
            r["_date"] = day(r["date"], where)
            r["_amt"] = money(r["amount"], where, q)
            r["_side"] = side
            r["_ref"] = norm(r.get("reference", ""))
            r["_fitid"] = r.get("fitid", "").strip()
            r["_carried"] = False
            rows.append(r)
        return rows


def load_balances(path, q):
    if not os.path.isfile(path):
        raise InputError(f"balances: file not found: {path}")
    try:
        with open(path, encoding="utf-8-sig") as fh:
            b = json.load(fh)
    except json.JSONDecodeError as exc:
        raise InputError(f"balances.json ({path}): not valid JSON ({exc.msg}, line {exc.lineno} column {exc.colno}). "
                         "Rebuild it from templates/balances.json.")
    if not isinstance(b, dict):
        raise InputError(f"balances.json ({path}): must be one JSON object. Rebuild it from templates/balances.json.")
    for k in ("window_days", "stale_days"):
        if k in b:
            try:
                n = int(str(b[k]).strip())
            except ValueError:
                raise InputError(f"balances.json {k}: '{b[k]}' is not a whole number of days (for example 3).")
            if n < 0:
                raise InputError(f"balances.json {k}: '{b[k]}' must be 0 or more days.")
            b[k] = n
    need = ["account", "currency", "period_start", "period_end", "statement_opening",
            "statement_closing", "ledger_opening", "ledger_closing"]
    missing = [k for k in need if k not in b]
    if missing:
        raise InputError(f"balances.json: missing {missing}. See references/input-schema.md.")
    out = dict(b)
    for k in ["statement_opening", "statement_closing", "ledger_opening", "ledger_closing"]:
        out[k] = money(b[k], f"balances.json {k}", q)
    if b.get("prior_approved_closing") not in (None, ""):
        out["prior_approved_closing"] = money(b["prior_approved_closing"], "balances.json prior_approved_closing", q)
    else:
        out["prior_approved_closing"] = None
    out["period_start"] = day(b["period_start"], "balances.json period_start")
    out["period_end"] = day(b["period_end"], "balances.json period_end")
    if re.search(r"\d{5,}", str(b["account"])):
        raise InputError("balances.json account: shows 5 or more digits. Use a label with the last 4 only, e.g. main-4411.")
    return out


# ---------------------------------------------------------------- matching

class Matcher:
    def __init__(self, stmt, ledg, window):
        self.s = {r["id"]: r for r in stmt}
        self.l = {r["id"]: r for r in ledg}
        self.window = window
        self.matches = []
        self.ambiguous = {}

    def _near(self, a, b):
        if a["_carried"] or b["_carried"]:
            return True
        return abs((a["_date"] - b["_date"]).days) <= self.window

    def run_pass(self, name, pred):
        s_ids = list(self.s)
        for sid in s_ids:
            if sid not in self.s:
                continue
            srow = self.s[sid]
            cands = [lid for lid, lrow in self.l.items() if pred(srow, lrow)]
            if not cands:
                continue
            if len(cands) == 1:
                lrow = self.l[cands[0]]
                back = [x for x, xrow in self.s.items() if pred(xrow, lrow)]
                if len(back) == 1:
                    self._take(name, [sid], cands)
                    self.ambiguous.pop(sid, None)
                    continue
                cands = cands + [f"(also statement {x})" for x in back if x != sid]
            self.ambiguous[sid] = (name, cands)

    def _take(self, name, sids, lids):
        amount = sum((self.s[x]["_amt"] for x in sids), Decimal(0))
        self.matches.append({"pass": name, "statement_ids": ";".join(sids),
                             "ledger_ids": ";".join(lids), "amount": str(amount)})
        for x in sids:
            self.s.pop(x)
        for x in lids:
            self.l.pop(x)

    def batch_pass(self):
        # One statement line = several ledger rows sharing one reference, or the reverse.
        for big, small, big_is_s in ((self.s, self.l, True), (self.l, self.s, False)):
            groups = {}
            for rid, r in small.items():
                if r["_ref"]:
                    groups.setdefault(r["_ref"], []).append(rid)
            for bid in list(big):
                if bid not in big:
                    continue
                brow = big[bid]
                for ref, ids in groups.items():
                    ids = [i for i in ids if i in small]
                    if not (2 <= len(ids) <= MAX_BATCH):
                        continue
                    if not (brow["_ref"] == ref or ref in norm(brow.get("description", ""))):
                        continue
                    total = sum((small[i]["_amt"] for i in ids), Decimal(0))
                    if total != brow["_amt"] or not all(self._near(brow, small[i]) for i in ids):
                        continue
                    if big_is_s:
                        self._take("batch (shared reference)", [bid], ids)
                    else:
                        self._take("batch (shared reference)", ids, [bid])
                    break

    def run(self):
        eq = lambda a, b: a["_amt"] == b["_amt"]
        self.run_pass("1 bank id (FITID)", lambda a, b: eq(a, b) and a["_fitid"] and a["_fitid"] == b["_fitid"])
        self.run_pass("2 date+amount+reference", lambda a, b: eq(a, b) and a["_date"] == b["_date"] and a["_ref"] and a["_ref"] == b["_ref"])
        self.run_pass("3 date+amount, unique", lambda a, b: eq(a, b) and a["_date"] == b["_date"])
        self.run_pass("4 window+amount+reference", lambda a, b: eq(a, b) and self._near(a, b) and a["_ref"] and a["_ref"] == b["_ref"])
        self.run_pass("5 window+amount, unique", lambda a, b: eq(a, b) and self._near(a, b))
        self.batch_pass()
        for sid in list(self.ambiguous):
            if sid not in self.s:
                self.ambiguous.pop(sid)


# ---------------------------------------------------------------- diagnostics

def digits(x):
    return re.sub(r"\D", "", str(abs(x)))


def adjacent_swap(a, b):
    da, db = digits(a), digits(b)
    if len(da) != len(db) or da == db:
        return False
    diff = [i for i in range(len(da)) if da[i] != db[i]]
    return len(diff) == 2 and diff[1] == diff[0] + 1 and da[diff[0]] == db[diff[1]] and da[diff[1]] == db[diff[0]]


def duplicates(rows):
    by_fitid, by_key = {}, {}
    for r in rows:
        if r["_fitid"]:
            by_fitid.setdefault(r["_fitid"], []).append(r["id"])
        key = (r["_date"], r["_amt"], norm(r.get("description", "")))
        by_key.setdefault(key, []).append(r["id"])
    out = []
    for k, ids in by_fitid.items():
        if len(ids) > 1:
            out.append(("same bank id (FITID)", k, ids))
    for k, ids in by_key.items():
        if len(ids) > 1:
            out.append(("same date+amount+description", f"{k[0]} {k[1]}", ids))
    return out


# ---------------------------------------------------------------- core

def reconcile(a, q):
    bal = load_balances(a.balances, q)
    ps, pe = bal["period_start"], bal["period_end"]
    stmt_all = read_rows(a.statement, "statement", q)
    ledg_all = read_rows(a.ledger, "ledger", q)
    carried = read_rows(a.carried, "carried", q, need=("side", "id", "date", "amount")) if a.carried else []
    window = int(bal.get("window_days", DEFAULT_WINDOW_DAYS) if a.window is None else a.window)
    # Age after which an uncleared ledger row, or a late-clearing one, is stale.
    # Owner setting "stale_days" in balances.json; without it the matching window
    # is used (never looser than before).
    stale_days = int(bal.get("stale_days", window))

    in_p = lambda r: ps <= r["_date"] <= pe
    stmt = [r for r in stmt_all if in_p(r)]
    ledg = [r for r in ledg_all if in_p(r)]
    out_of_period = [r for r in stmt_all + ledg_all if not in_p(r)]

    stops, notes = [], []
    # Control 1: each input proves to its own closing balance.
    s_sum = sum((r["_amt"] for r in stmt), Decimal(0))
    l_sum = sum((r["_amt"] for r in ledg), Decimal(0))
    for name, opening, total, closing in (
        ("statement", bal["statement_opening"], s_sum, bal["statement_closing"]),
        ("ledger", bal["ledger_opening"], l_sum, bal["ledger_closing"]),
    ):
        if opening + total != closing:
            flipped = opening - total == closing
            stops.append(
                f"{name} does not prove: opening {opening} + in-period lines {total} = {opening + total}, "
                f"but closing is {closing}. "
                + ("The sign convention is reversed: flip the amount column (see references/input-schema.md)."
                   if flipped else "Lines are missing or duplicated, or the export covers different dates. Get a complete export.")
            )
    # Control 2: period chaining.
    prior = bal["prior_approved_closing"]
    if prior is None:
        notes.append("No prior approved closing supplied: first period, or the prior reconciliation is not approved. Record as an open item.")
    elif prior != bal["statement_opening"]:
        stops.append(
            f"Statement opening {bal['statement_opening']} does not equal the prior approved closing {prior} "
            f"(difference {bal['statement_opening'] - prior}). Suspect an edit to a reconciled period or the wrong statement. "
            "Do not undo or re-reconcile anything; report it to the owner."
        )
    if stops and not a.diagnose:
        raise StopControl("\n".join(stops))

    # Carried ids are namespaced "carried:<originated>:<id>" so a carried row can
    # never replace this period's row with the same id (March line 3 vs April
    # line 3). carried-next.csv keeps the namespaced id, so it is not re-prefixed.
    current_ids = {"statement": {r["id"] for r in stmt_all}, "ledger": {r["id"] for r in ledg_all}}
    carried_alias, carried_ids = {}, set()
    for r in carried:
        side = r.get("side", "").lower()
        if side not in ("statement", "ledger"):
            raise InputError(f"carried id {r['id']}: side must be statement or ledger")
        r["_carried"] = True
        r["_side"] = side
        orig = r["id"]
        if not orig.startswith("carried:"):
            r["id"] = f"carried:{r.get('originated') or str(r['_date'])[:7]}:{orig}"
        if r["id"] in current_ids[side] or (side, r["id"]) in carried_ids:
            raise InputError(f"carried id '{r['id']}' collides with another {side} id. Give each carried row a unique id.")
        carried_ids.add((side, r["id"]))
        carried_alias.setdefault((side, orig.split(":")[-1]), []).append(r["id"])

    def resolve(side, rid):
        # classify.csv may name a carried row by its namespaced id, or by its
        # original id when no current row on that side uses it.
        if rid in current_ids.get(side, set()) or (side, rid) in carried_ids:
            return rid
        hits = carried_alias.get((side, rid), [])
        return hits[0] if len(hits) == 1 else rid
    m = Matcher(stmt + [r for r in carried if r["_side"] == "statement"],
                ledg + [r for r in carried if r["_side"] == "ledger"], window)
    m.run()

    # Human classifications.
    cls_s, cls_l, pairs = {}, {}, []
    if a.classify:
        for r in read_rows_plain(a.classify, ("side", "id", "class")):
            side, rid, c = r["side"].lower(), r["id"], r["class"].lower()
            rid = resolve(side, rid)
            if side == "statement":
                if c not in STATEMENT_CLASSES:
                    raise InputError(f"classify {rid}: statement class must be one of {sorted(STATEMENT_CLASSES)}")
                if c in ("ledger-error", "match"):
                    pid = resolve("ledger", r.get("pair_id", ""))
                    if rid not in m.s or pid not in m.l:
                        raise InputError(f"classify {rid}: '{c}' needs an unmatched statement id and an unmatched ledger pair_id ('{pid}').")
                    if c == "match" and m.s[rid]["_amt"] != m.l[pid]["_amt"]:
                        raise InputError(f"classify {rid}: a confirmed match needs equal amounts; use ledger-error for a wrong amount.")
                    pairs.append((c, rid, pid, r.get("note", "")))
                else:
                    cls_s[rid] = (c, r.get("note", ""))
            elif side == "ledger":
                if c not in LEDGER_CLASSES:
                    raise InputError(f"classify {rid}: ledger class must be one of {sorted(LEDGER_CLASSES)}")
                cls_l[rid] = (c, r.get("note", ""))
            else:
                raise InputError(f"classify {rid}: side must be statement or ledger")

    pair_adjust = Decimal(0)
    pair_rows = []
    for c, sid, lid, note in pairs:
        s_amt, l_amt = m.s[sid]["_amt"], m.l[lid]["_amt"]
        if c == "match":
            m._take(f"manual, confirmed ({note or 'no note'})", [sid], [lid])
        else:
            pair_adjust += s_amt - l_amt
            pair_rows.append({"statement_id": sid, "ledger_id": lid, "statement_date": str(m.s[sid]["_date"]),
                              "ledger_date": str(m.l[lid]["_date"]), "statement_amount": str(s_amt),
                              "ledger_amount": str(l_amt), "correction": str(s_amt - l_amt), "note": mask(note)})
            m.s.pop(sid)
            m.l.pop(lid)

    dup_groups = duplicates(stmt) + duplicates(ledg)
    dup_ids = {i for _, _, ids in dup_groups for i in ids}

    def s_class(r):
        if r["id"] in cls_s:
            return cls_s[r["id"]]
        if r["_carried"] and r.get("class"):
            return (r["class"].lower(), "carried")
        return ("investigate", "default: cause unknown")

    # Timing confirmation against the next statement.
    cleared = {}
    if a.next_statement:
        nxt = read_rows(a.next_statement, "next-statement", q)
        used = set()
        for lid, lrow in m.l.items():
            hits = [n for n in nxt if n["id"] not in used and n["_amt"] == lrow["_amt"]
                    and (not lrow["_ref"] or n["_ref"] == lrow["_ref"] or lrow["_ref"] in norm(n.get("description", "")))]
            if len(hits) == 1:
                cleared[lid] = str(hits[0]["_date"])
                used.add(hits[0]["id"])

    def l_class(r):
        # A ledger-only row is presumed timing only while it is fresh: dated within
        # the matching window of period end, or confirmed cleared on the next
        # statement. Anything older is investigate, never a silent plug.
        if r["id"] in cls_l:
            return cls_l[r["id"]]
        if r["id"] in dup_ids:
            return ("investigate", "default: possible duplicate")
        kind = "deposit in transit" if r["_amt"] > 0 else "payment outstanding"
        if r["_carried"]:
            if r.get("class") and r["class"].lower() not in ("timing", ""):
                return (r["class"].lower(), "carried")
            # A timing item open last period that has still not cleared on this statement.
            return ("investigate", f"default: stale timing item: carried {kind} did not clear this period")
        if r["id"] in cleared:
            return ("timing", "default: unconfirmed until it clears")
        age = (pe - r["_date"]).days
        if age > stale_days:
            return ("investigate", f"default: stale timing item: {kind} older than {stale_days} days at period end and not confirmed cleared")
        return ("timing", "default: unconfirmed until it clears")

    # Late clearing is a lapping signal only for money in (a deposit recorded in
    # the books that reaches the bank days later). A payment, such as a cheque
    # the payee banks a week later, is routine: its lag is noted, not escalated.
    # The lag is in calendar days, so a bank-holiday weekend counts.
    late, slow_pay = {}, {}
    for lid, when in cleared.items():
        lag = (dt.date.fromisoformat(when) - m.l[lid]["_date"]).days
        if lag > stale_days:
            (late if m.l[lid]["_amt"] > 0 else slow_pay)[lid] = lag

    uns, unl = [], []
    adj_stmt, adj_ledg = bal["statement_closing"], bal["ledger_closing"] + pair_adjust
    investigate_total = Decimal(0)
    for r in m.s.values():
        c, why = s_class(r)
        if c == "correction":
            adj_ledg += r["_amt"]
        elif c == "bank-error":
            adj_stmt -= r["_amt"]
        else:
            investigate_total += r["_amt"]
        uns.append(row_out(r, c, why, None))
    for r in m.l.values():
        c, why = l_class(r)
        if c == "timing":
            adj_stmt += r["_amt"]
            if r["id"] in cleared:
                why = f"cleared on next statement {cleared[r['id']]}"
                if r["id"] in late:
                    why += (f"; late clearing: deposit reached the bank {late[r['id']]} calendar days after the ledger date "
                            f"(stale after {stale_days}); step 7 escalation")
                elif r["id"] in slow_pay:
                    why += f"; payment cleared {slow_pay[r['id']]} calendar days after the ledger date (routine; no escalation)"
        elif c == "correction":
            adj_ledg -= r["_amt"]
        else:
            investigate_total -= r["_amt"]
        unl.append(row_out(r, c, why, cleared.get(r["id"])))

    unexplained = (adj_stmt - adj_ledg).quantize(q)
    diag = []
    if unexplained != 0:
        cents = abs(int((unexplained / q).to_integral_value()))
        if cents % 9 == 0:
            diag.append(f"Difference {unexplained} divides by 9: look for a transposed amount first (for example 95.00 keyed as 59.00).")
        half = (abs(unexplained) / 2).quantize(q)
        for r in list(m.s.values()) + list(m.l.values()):
            if abs(r["_amt"]) == half:
                diag.append(f"Half the difference ({half}) equals {r['_side']} {r['id']}: possible sign error (entered on the wrong side).")
    for sr in m.s.values():
        for lr in m.l.values():
            if adjacent_swap(sr["_amt"], lr["_amt"]) and (sr["_amt"] > 0) == (lr["_amt"] > 0):
                diag.append(f"Transposition candidate: statement {sr['id']} {sr['_amt']} vs ledger {lr['id']} {lr['_amt']} "
                            f"(difference {sr['_amt'] - lr['_amt']}). If confirmed, classify as ledger-error with pair_id.")
    for r in out_of_period:
        if unexplained != 0 and abs(r["_amt"]) == abs(unexplained):
            diag.append(f"Out-of-period {r['_side']} row {r['id']} ({r['_date']}, {r['_amt']}) equals the unexplained difference. "
                        "It is NOT eligible. Never pull a transaction from another period to close a gap.")
    if dup_groups:
        diag.append(f"{len(dup_groups)} duplicate group(s) found; see duplicates.csv. Recommend Exclude (not delete) for feed duplicates; the owner performs it.")
    if m.ambiguous:
        diag.append(f"{len(m.ambiguous)} statement line(s) had more than one possible partner and were left unmatched; see ambiguous.csv.")
    late_rows = [r for r in unl if r["class"] == "timing" and "late clearing" in r["why"]]
    if late_rows:
        diag.append(f"{len(late_rows)} deposit(s) in transit reached the bank on the next statement more than {stale_days} calendar days "
                    f"after the ledger date ({', '.join(r['id'] for r in late_rows)}). Late-clearing deposits are a lapping signal: "
                    "escalate (step 7)"
                    + ("." if "stale_days" in bal else "; the threshold is the matching-window default, not confirmed with the owner "
                       "(a deposit made before a bank-holiday weekend can trip it)."))

    blocking = [r for r in uns + unl if r["class"] == "investigate"]
    status = "RECONCILED" if unexplained == 0 and not stops and not blocking else "NOT RECONCILED"
    if stops:
        status = "STOPPED"
    summary = {
        "account": bal["account"], "currency": bal["currency"],
        "period": f"{ps} to {pe}", "window_days": window,
        "window_days_note": "default — confirm with the owner" if a.window is None and "window_days" not in bal else "as supplied",
        "stale_days": stale_days,
        "stale_days_note": "as supplied" if "stale_days" in bal else "defaults to the matching window — confirm with the owner",
        "late_clearing_items": len(late_rows),
        "statement_opening": str(bal["statement_opening"]), "statement_closing": str(bal["statement_closing"]),
        "ledger_opening": str(bal["ledger_opening"]), "ledger_closing": str(bal["ledger_closing"]),
        "prior_approved_closing": None if prior is None else str(prior),
        "statement_lines_in_period": len(stmt), "ledger_rows_in_period": len(ledg),
        "statement_credits": str(sum((r["_amt"] for r in stmt if r["_amt"] > 0), Decimal(0))),
        "statement_debits": str(sum((r["_amt"] for r in stmt if r["_amt"] < 0), Decimal(0))),
        "ledger_credits": str(sum((r["_amt"] for r in ledg if r["_amt"] > 0), Decimal(0))),
        "ledger_debits": str(sum((r["_amt"] for r in ledg if r["_amt"] < 0), Decimal(0))),
        "matched_groups": len(m.matches),
        "matched_value": str(sum((Decimal(x["amount"]) for x in m.matches), Decimal(0))),
        "deposits_in_transit": str(sum((Decimal(r["amount"]) for r in unl if r["class"] == "timing" and Decimal(r["amount"]) > 0), Decimal(0))),
        "outstanding_payments": str(sum((Decimal(r["amount"]) for r in unl if r["class"] == "timing" and Decimal(r["amount"]) < 0), Decimal(0))),
        "adjusted_statement_balance": str(adj_stmt.quantize(q)),
        "adjusted_ledger_balance": str(adj_ledg.quantize(q)),
        "unexplained_difference": str(unexplained),
        "investigate_items": len(blocking),
        "status": status, "stops": stops, "notes": notes, "diagnostics": diag,
        "script": "statement-reconciliation/scripts/rec_match.py",
    }
    return summary, m, uns, unl, dup_groups, out_of_period, pair_rows


def row_out(r, c, why, cleared):
    return {"side": r["_side"], "id": r["id"], "date": str(r["_date"]), "amount": str(r["_amt"]),
            "description": mask(r.get("description", "")), "reference": mask(r.get("reference", "")),
            "carried": "yes" if r["_carried"] else "", "originated": r.get("originated", "") or str(r["_date"])[:7],
            "class": c, "why": why, "cleared_on": cleared or "", "owner": r.get("owner", ""), "next_step": r.get("next_step", "")}


def read_rows_plain(path, need):
    if not os.path.isfile(path):
        raise InputError(f"file not found: {path}")
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        cols = [c.strip().lower() for c in rd.fieldnames or []]
        if any(n not in cols for n in need):
            raise InputError(f"{os.path.basename(path)}: needs columns {list(need)}, found {cols}")
        return [{k.strip().lower(): (v or "").strip() for k, v in row.items() if k} for row in rd]


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_outputs(out, summary, m, uns, unl, dups, oop, pairs):
    os.makedirs(out, exist_ok=True)
    unf = ["side", "id", "date", "amount", "description", "reference", "carried", "originated", "class", "why", "cleared_on", "owner", "next_step"]
    write_csv(os.path.join(out, "matches.csv"), m.matches, ["pass", "statement_ids", "ledger_ids", "amount"])
    write_csv(os.path.join(out, "unmatched_statement.csv"), uns, unf)
    write_csv(os.path.join(out, "unmatched_ledger.csv"), unl, unf)
    write_csv(os.path.join(out, "duplicates.csv"),
              [{"rule": a, "key": str(k), "ids": ";".join(ids)} for a, k, ids in dups], ["rule", "key", "ids"])
    write_csv(os.path.join(out, "ambiguous.csv"),
              [{"statement_id": s, "pass": p, "candidates": ";".join(c)} for s, (p, c) in m.ambiguous.items()],
              ["statement_id", "pass", "candidates"])
    write_csv(os.path.join(out, "out_of_period.csv"),
              [{"side": r["_side"], "id": r["id"], "date": str(r["_date"]), "amount": str(r["_amt"]),
                "description": mask(r.get("description", ""))} for r in oop],
              ["side", "id", "date", "amount", "description"])
    write_csv(os.path.join(out, "ledger_errors.csv"), pairs,
              ["statement_id", "ledger_id", "statement_date", "ledger_date", "statement_amount", "ledger_amount", "correction", "note"])
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


def print_summary(s):
    print(f"{s['status']}: {s['account']} {s['period']} ({s['currency']})")
    print(f"  adjusted statement {s['adjusted_statement_balance']}  adjusted ledger {s['adjusted_ledger_balance']}  "
          f"unexplained {s['unexplained_difference']}")
    print(f"  statement in {s['statement_credits']} out {s['statement_debits']}; ledger in {s['ledger_credits']} out {s['ledger_debits']}")
    print(f"  matched groups {s['matched_groups']} value {s['matched_value']}; "
          f"in transit {s['deposits_in_transit']}; outstanding {s['outstanding_payments']}; investigate {s['investigate_items']}")
    for line in s["stops"] + s["notes"] + s["diagnostics"]:
        print(f"  - {line}")


# ---------------------------------------------------------------- selftest

def selftest(q):
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(os.path.dirname(here), "examples", "scenarios")
    failures = 0
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        exp_path = os.path.join(d, "expected.json")
        if not os.path.isfile(exp_path):
            continue
        with open(exp_path, encoding="utf-8") as fh:
            spec = json.load(fh)
        if "runs" not in spec:
            continue  # another script's fixture (payout_breakdown.py)
        for run in spec["runs"]:
            p = lambda f: os.path.join(d, f) if f else None
            ns = argparse.Namespace(statement=p("statement.csv"), ledger=p("ledger.csv"),
                                    balances=p(run.get("balances", "balances.json")),
                                    carried=p(run.get("carried")), classify=p(run.get("classify")),
                                    next_statement=p(run.get("next_statement")), window=None, diagnose=False)
            try:
                got = reconcile(ns, q)[0]
            except StopControl:
                got = {"status": "STOPPED"}
            bad = {k: (v, got.get(k)) for k, v in run["expect"].items() if got.get(k) != v}
            label = f"{name} [{run.get('label', '')}]"
            if bad:
                failures += 1
                print(f"FAIL {label}: {bad}")
            else:
                print(f"ok   {label}")
    # Late clearing: the 4,000.00 deposit of 3 April reaches the bank on 20 May.
    # It stays timing (the next statement proves it) but is flagged for step 7.
    d = os.path.join(root, "g-stale-timing")
    with tempfile.TemporaryDirectory() as tmp:
        nxt = os.path.join(tmp, "next.csv")
        with open(os.path.join(d, "next-statement.csv"), encoding="utf-8") as fh:
            body = fh.read().rstrip("\n") + "\nN3,2026-05-20,4000.00,CASH DEPOSIT,,F1103\n"
        with open(nxt, "w", encoding="utf-8") as fh:
            fh.write(body)
        ns = argparse.Namespace(statement=os.path.join(d, "statement.csv"), ledger=os.path.join(d, "ledger.csv"),
                                balances=os.path.join(d, "balances.json"), carried=None,
                                classify=os.path.join(d, "classify.csv"), next_statement=nxt, window=None, diagnose=False)
        got, _, _, unl, _, _, _ = reconcile(ns, q)
        l9 = [r for r in unl if r["id"] == "L9"][0]
        if got["late_clearing_items"] != 1 or "late clearing: deposit reached the bank 47 calendar days" not in l9["why"] \
                or not any("lapping" in x for x in got["diagnostics"]):
            failures += 1
            print(f"FAIL late clearing: {got['late_clearing_items']} {l9['why']}")
        else:
            print("ok   late clearing is flagged for escalation")
        # A cheque the payee banks 8 days later is routine: noted, never a lapping escalation.
        lg = os.path.join(tmp, "ledger.csv")
        with open(os.path.join(d, "ledger.csv"), encoding="utf-8") as fh:
            w = fh.read().rstrip("\n") + "\nLC1,2026-04-28,-450.00,Cheque 000812,000812,\n"
        with open(lg, "w", encoding="utf-8") as fh:
            fh.write(w)
        with open(os.path.join(d, "balances.json"), encoding="utf-8") as fh:
            b = json.load(fh)
        b["ledger_closing"] = str(Decimal(str(b["ledger_closing"])) - Decimal("450.00"))
        bj = os.path.join(tmp, "bal.json")
        with open(bj, "w", encoding="utf-8") as fh:
            json.dump(b, fh)
        nxt2 = os.path.join(tmp, "next2.csv")
        with open(os.path.join(d, "next-statement.csv"), encoding="utf-8") as fh:
            body = fh.read().rstrip("\n") + "\nN4,2026-05-06,-450.00,CHQ 000812,000812,F1104\n"
        with open(nxt2, "w", encoding="utf-8") as fh:
            fh.write(body)
        ns = argparse.Namespace(statement=os.path.join(d, "statement.csv"), ledger=lg, balances=bj, carried=None,
                                classify=os.path.join(d, "classify.csv"), next_statement=nxt2, window=None, diagnose=False)
        got, _, _, unl, _, _, _ = reconcile(ns, q)
        lc = [r for r in unl if r["id"] == "LC1"][0]
        if lc["class"] != "timing" or "late clearing" in lc["why"] or "routine" not in lc["why"] or got["late_clearing_items"] != 0 \
                or any("lapping" in x for x in got["diagnostics"]):
            failures += 1
            print(f"FAIL late cheque: {lc['class']} {lc['why']} {got['diagnostics']}")
        else:
            print("ok   a late-clearing cheque is noted, not escalated")
        # Malformed balances.json is a fix-it message (exit 2), not a traceback.
        bad = os.path.join(tmp, "bad.json")
        for text in ("{bad json", '{"window_days": "three"}'):
            with open(bad, "w", encoding="utf-8") as fh:
                fh.write(text)
            try:
                load_balances(bad, q)
                failures += 1
                print(f"FAIL malformed balances accepted: {text}")
            except InputError:
                print(f"ok   malformed balances refused: {text}")
    print("selftest ok" if not failures else f"selftest FAILED ({failures})")
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--statement")
    p.add_argument("--ledger")
    p.add_argument("--balances")
    p.add_argument("--carried", help="prior open items still uncleared (side,id,date,amount,...)")
    p.add_argument("--classify", help="human classifications of unmatched items (side,id,class,pair_id,note)")
    p.add_argument("--next-statement", help="next period's statement lines, to confirm timing items cleared")
    p.add_argument("--window", type=int, default=None, help=f"days; default {DEFAULT_WINDOW_DAYS} (confirm with the owner)")
    p.add_argument("--minor-units", type=int, default=2, help="decimal places of the currency (JPY 0, most others 2)")
    p.add_argument("--diagnose", action="store_true", help="continue past a STOP control to produce lists; status stays STOPPED")
    p.add_argument("--out")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    q = Decimal(1).scaleb(-a.minor_units)
    if a.selftest:
        return selftest(q)
    if not (a.statement and a.ledger and a.balances and a.out):
        p.error("--statement, --ledger, --balances and --out are required")
    try:
        result = reconcile(a, q)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except StopControl as exc:
        print("STOPPED: a control failed. Nothing was matched.\n" + str(exc))
        print("Report this to the owner. Re-run with --diagnose only to list items for the investigation.")
        return 3
    write_outputs(a.out, *result)
    print_summary(result[0])
    print(f"  files: {a.out}")
    return 3 if result[0]["status"] == "STOPPED" else 0


if __name__ == "__main__":
    sys.exit(main())
