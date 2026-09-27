#!/usr/bin/env python3
"""Offer arithmetic from an approved band. Computes; never proposes a figure.

Usage (run from the package dir: cd ~/skills/job-offer-and-close-plan):

  python3 scripts/offer_math.py --band-min 95000 --band-max 110000 --currency EUR \
      --band-approver "Lena Ortiz + finance" --band-approved-on 2026-09-01 \
      --base 104000 [--bonus-pct 10 | --bonus-amount 8000] [--signing 0] \
      [--variable-target 40000]            # sales: on-target variable pay
      [--offer-base 104000 --offer-signing 0 --offer-bonus-pct 10]   # terms as extended
      [--ask-base 112000 --ask-signing 5000 --ask-bonus-pct 10]      # candidate's counter
      [--proposal-base 108000 --proposal-signing 0]                  # owner's paired give
      [--walk-away 108000]                 # owner-set line inside the band
      [--equity-text "0.15% options, standard vesting"]
      [--json out.json]

Inputs: every figure must come from the owner or approver (the band and who
approved it) or from the candidate's own words (the ask). Never pass current or
past pay: there is deliberately no flag for it.

Outputs: a markdown block on stdout (paste it into the offer brief) and, with
--json, the same numbers machine-readable.

Exit codes: 0 ok; 1 the base or the proposal is above band max, or the
proposal is above the owner's walk-away line (the table still prints; the
figure may not go in the brief or to the candidate without the approver's
written yes); 2 bad input; 3 no approved band or no approver (ask for them).
The JSON key "recommended" holds the owner-supplied composition; the script
never proposes a figure.
Nothing here estimates, benchmarks, or looks up market data. Equity is carried
as text only: its value depends on strike, valuation and vesting that the
approver supplies in words.
"""

import argparse
import json
import sys


def money(value, currency):
    if value is None:
        return "-"
    return f"{currency} {value:,.0f}"


def pct(value):
    return "-" if value is None else f"{value:.1f}%"


def bonus_value(base, bonus_pct, bonus_amount):
    if bonus_amount is not None:
        return bonus_amount
    if bonus_pct is not None and base is not None:
        return base * bonus_pct / 100.0
    return None


def package(base, bonus_pct, bonus_amount, signing, variable):
    """First-year cash (base + target bonus + signing) and OTE when sales."""
    if base is None:
        return None
    bonus = bonus_value(base, bonus_pct, bonus_amount) or 0.0
    return {
        "base": base,
        "target_bonus": bonus,
        "signing": signing or 0.0,
        "on_target_variable": variable,
        "ote": base + variable if variable is not None else None,
        "first_year_cash": base + bonus + (signing or 0.0) + (variable or 0.0),
    }


def band_position(value, lo, hi):
    if value is None:
        return None
    return (value - lo) / (hi - lo) * 100.0 if hi > lo else None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--band-min", type=float)
    p.add_argument("--band-max", type=float)
    p.add_argument("--currency", default="")
    p.add_argument("--band-approver", default="")
    p.add_argument("--band-approved-on", default="")
    p.add_argument("--base", type=float, help="base for the brief, as the owner supplies it")
    p.add_argument("--bonus-pct", type=float)
    p.add_argument("--bonus-amount", type=float)
    p.add_argument("--signing", type=float, default=0.0)
    p.add_argument("--variable-target", type=float, help="sales: approved on-target variable")
    for who in ("offer", "ask", "proposal"):
        p.add_argument(f"--{who}-base", type=float)
        p.add_argument(f"--{who}-signing", type=float)
        p.add_argument(f"--{who}-bonus-pct", type=float)
        p.add_argument(f"--{who}-variable", type=float)
    p.add_argument("--walk-away", type=float, help="owner-set line inside the band")
    p.add_argument("--equity-text", default="")
    p.add_argument("--json")
    a = p.parse_args(argv)

    if a.band_min is None or a.band_max is None or not a.band_approver.strip():
        print("STOP: no approved band or no approver. Ask the owner for the approved "
              "band (min and max) and who approved it. Do not estimate one.", file=sys.stderr)
        return 3
    if not a.currency:
        print("error: --currency is required (e.g. EUR, USD, GBP).", file=sys.stderr)
        return 2
    if a.band_max < a.band_min:
        print("error: --band-max must not be below --band-min (use the same figure for both "
              "when a single amount was approved).", file=sys.stderr)
        return 2
    if a.bonus_pct is not None and a.bonus_amount is not None:
        print("error: give --bonus-pct or --bonus-amount, not both.", file=sys.stderr)
        return 2
    if a.walk_away is not None and not (a.band_min <= a.walk_away <= a.band_max):
        print("error: --walk-away must sit inside the approved band.", file=sys.stderr)
        return 2

    cur, lo, hi = a.currency, a.band_min, a.band_max
    mid = (lo + hi) / 2.0
    ceiling = a.walk_away if a.walk_away is not None else hi
    over_limit = False
    out = {
        "band": {"min": lo, "max": hi, "midpoint": mid, "currency": cur,
                 "approver": a.band_approver, "approved_on": a.band_approved_on},
        "ceiling": {"value": ceiling, "basis": "owner walk-away" if a.walk_away is not None else "band max"},
        "equity_text": a.equity_text,
        "flags": [],
    }

    lines = [f"Approved band: {money(lo, cur)} - {money(hi, cur)} base "
             f"(midpoint {money(mid, cur)}), approved by {a.band_approver}"
             + (f" on {a.band_approved_on}" if a.band_approved_on else "") + ".",
             f"Ceiling for any give: {money(ceiling, cur)} ({out['ceiling']['basis']})."]
    if hi == lo:
        lines.append("Single approved figure (min = max): position in band is n/a; "
                     "any give above it needs the approver.")

    if a.base is not None:
        pos = band_position(a.base, lo, hi)
        pk = package(a.base, a.bonus_pct, a.bonus_amount, a.signing, a.variable_target)
        out["recommended"] = dict(pk, band_position_pct=pos,
                                  pct_of_midpoint=a.base / mid * 100.0,
                                  room_to_ceiling=ceiling - a.base)
        lines += ["", "| Composition (owner-supplied) | Value |", "|---|---|",
                  f"| Base | {money(a.base, cur)} |",
                  f"| Position in band | {pct(pos)} (0% = min, 100% = max) |",
                  f"| Base as % of midpoint | {pct(a.base / mid * 100.0)} |",
                  f"| Room to ceiling | {money(ceiling - a.base, cur)} |",
                  f"| Target bonus | {money(pk['target_bonus'], cur)} |",
                  f"| Signing | {money(pk['signing'], cur)} |"]
        if a.variable_target is not None:
            mix = a.base / pk["ote"] * 100.0
            lines += [f"| On-target variable | {money(a.variable_target, cur)} |",
                      f"| OTE (base + variable) | {money(pk['ote'], cur)} |",
                      f"| Pay mix | {mix:.0f}/{100 - mix:.0f} base/variable |"]
            out["recommended"]["pay_mix_base_pct"] = mix
        lines.append(f"| First-year cash at target | {money(pk['first_year_cash'], cur)} |")
        if a.equity_text:
            lines.append(f"| Equity (text as approved) | {a.equity_text} |")
        if a.base < lo:
            out["flags"].append(f"base is {money(lo - a.base, cur)} BELOW band min")
        if a.base > hi:
            over_limit = True
            out["flags"].append(f"base is {money(a.base - hi, cur)} ABOVE band max: needs approver sign-off before it goes in the brief")

    have_counter = any(getattr(a, f"{w}_base") is not None for w in ("offer", "ask", "proposal"))
    if have_counter:
        cols = []
        for who, label in (("offer", "Offer as extended"), ("ask", "Candidate ask (their words)"),
                           ("proposal", "Proposal (owner's give)")):
            base = getattr(a, f"{who}_base")
            if base is None:
                continue
            pk = package(base, getattr(a, f"{who}_bonus_pct"), None,
                         getattr(a, f"{who}_signing"), getattr(a, f"{who}_variable"))
            pk["band_position_pct"] = band_position(base, lo, hi)
            out[who] = pk
            cols.append((label, pk))
        lines += ["", "| Element | " + " | ".join(c[0] for c in cols) + " |",
                  "|---|" + "---|" * len(cols)]
        for key, name in (("base", "Base"), ("band_position_pct", "Position in band"),
                          ("target_bonus", "Target bonus"), ("signing", "Signing"),
                          ("ote", "OTE"), ("first_year_cash", "First-year cash")):
            if key == "ote" and all(c[1]["ote"] is None for c in cols):
                continue
            cells = [pct(c[1][key]) if key == "band_position_pct" else money(c[1][key], cur) for c in cols]
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
        if "ask" in out:
            gap_to_ceiling = out["ask"]["base"] - ceiling
            if out["ask"]["base"] > hi:
                out["flags"].append(f"ask base is {money(out['ask']['base'] - hi, cur)} ABOVE band max: escalate to the band approver; do not counter above band")
            elif gap_to_ceiling > 0:
                out["flags"].append(f"ask base is {money(gap_to_ceiling, cur)} above the owner's walk-away line (inside band): owner decides")
            if "offer" in out:
                out["ask_minus_offer_first_year"] = out["ask"]["first_year_cash"] - out["offer"]["first_year_cash"]
                lines.append(f"\nAsk minus offer, first-year cash: {money(out['ask_minus_offer_first_year'], cur)}.")
        if "proposal" in out:
            pb = out["proposal"]["base"]
            if pb > ceiling:
                over_limit = True
                out["flags"].append(f"proposal base exceeds the ceiling by {money(pb - ceiling, cur)}: not allowed without approver")
            if "offer" in out:
                out["give_first_year"] = out["proposal"]["first_year_cash"] - out["offer"]["first_year_cash"]
                lines.append(f"Paired give (proposal minus offer, first-year cash): {money(out['give_first_year'], cur)}.")
            lines.append(f"Room left to ceiling after proposal: {money(ceiling - pb, cur)}.")

    if out["flags"]:
        lines += ["", "FLAGS:"] + [f"- {f}" for f in out["flags"]]
    lines += ["", "All figures are arithmetic on owner-supplied inputs; nothing estimated or benchmarked."]
    print("\n".join(lines))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
    return 1 if over_limit else 0


if __name__ == "__main__":
    sys.exit(main())
