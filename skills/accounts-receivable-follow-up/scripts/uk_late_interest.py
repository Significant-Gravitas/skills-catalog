#!/usr/bin/env python3
"""Compute UK statutory late-payment interest and the fixed recovery sum for a
business-to-business debt. Use ONLY when the owner has opted in and confirmed
UK B2B, and there is no contract rate (a contract rate replaces the statutory
one [30][47]).

    cd ~/skills/accounts-receivable-follow-up && python3 scripts/uk_late_interest.py \
        --principal 2150.00 --due-date 2026-02-28 --calc-date 2026-04-30 \
        --reference-rate 3.75 --rate-source "Bank of England Bank Rate on 31 Dec 2025, <URL>, fetched <date>" \
        [--contract-rate 4]

Statutory rate = 8% + the reference rate [30]. The reference rate is the Bank
of England base rate fixed for each six months (the rate on 31 December for
January to June, on 30 June for July to December) [30]. It has NO default:
fetch it from the Bank of England with web_fetch, or ask the owner, and pass
its source. Daily interest = principal x rate / 365; interest = daily x days
late (calc date minus due date) [30].
Fixed sum per invoice by debt size [47]: under GBP 1,000 -> 40; 1,000 to
9,999.99 -> 70; 10,000 or more -> 100.
Figures checked against GOV.UK on 2026-09-27; confirm the page is unchanged.
Output is for the owner's decision. It is never put in a draft by default.
"""

import argparse
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

STATUTORY_UPLIFT = Decimal("8")   # percentage points over the reference rate [30]
BANDS = [(Decimal("1000"), Decimal("40")), (Decimal("10000"), Decimal("70")), (None, Decimal("100"))]  # [47]


def compute(principal, due, calc, reference_rate=None, contract_rate=None):
    days = (calc - due).days
    if days <= 0:
        raise bkio.InputError("the calculation date is not after the due date: nothing is late")
    if contract_rate is not None:
        rate, basis = contract_rate, "contract rate (replaces statutory interest)"
    elif reference_rate is not None:
        rate, basis = STATUTORY_UPLIFT + reference_rate, f"8% + reference rate {reference_rate}%"
    else:
        raise bkio.InputError("no rate: pass --reference-rate with --rate-source, or --contract-rate")
    daily = principal * rate / Decimal(100) / Decimal(365)
    interest = (daily * days).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    fixed = next(fee for limit, fee in BANDS if limit is None or principal < limit)
    return {"principal": str(principal), "days_late": days, "annual_rate_percent": str(rate), "basis": basis,
            "daily_interest": str(daily.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)),
            "interest_to_date": str(interest),
            "fixed_sum": str(fixed) if contract_rate is None else "check the contract",
            "note": "Statutory figures apply only to UK B2B debts with no contract rate; owner decides whether to claim."}


def selftest():
    from datetime import date
    r = compute(Decimal("2150.00"), date(2026, 2, 28), date(2026, 4, 30), reference_rate=Decimal("4"))
    # 61 days x 2150 x 12% / 365 = 43.12
    assert r["days_late"] == 61 and r["interest_to_date"] == "43.12", r
    assert r["fixed_sum"] == "70"
    assert compute(Decimal("999.99"), date(2026, 1, 1), date(2026, 1, 2), reference_rate=Decimal("4"))["fixed_sum"] == "40"
    assert compute(Decimal("10000"), date(2026, 1, 1), date(2026, 1, 2), reference_rate=Decimal("4"))["fixed_sum"] == "100"
    try:
        compute(Decimal("100"), date(2026, 1, 1), date(2026, 2, 1))
        raise AssertionError("no rate must fail")
    except bkio.InputError:
        pass
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--principal")
    ap.add_argument("--due-date")
    ap.add_argument("--calc-date")
    ap.add_argument("--reference-rate")
    ap.add_argument("--rate-source")
    ap.add_argument("--contract-rate")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.principal and a.due_date and a.calc_date):
        bkio.die("--principal, --due-date and --calc-date are required")
    if a.reference_rate and not a.rate_source:
        bkio.die("--reference-rate needs --rate-source", "quote the Bank of England page and fetch date, or 'owner stated'")
    try:
        r = compute(bkio.parse_amount(a.principal)[0], bkio.parse_iso(a.due_date), bkio.parse_iso(a.calc_date),
                    Decimal(a.reference_rate) if a.reference_rate else None,
                    Decimal(a.contract_rate) if a.contract_rate else None)
    except bkio.InputError as e:
        bkio.die(str(e))
    for k, v in r.items():
        print(f"{k}: {v}")
    if a.rate_source:
        print(f"rate_source: {a.rate_source}")


if __name__ == "__main__":
    main()
