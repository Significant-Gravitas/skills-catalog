"""Shared pay-history detector for check_terms.py and fill_offer_template.py.

It catches common phrasings of current or past pay in a term's value, source
or notes. It is a backstop, not the rule: the rule (never ask for, record or
use current or past pay, even volunteered) is applied by whoever writes the
terms. A phrasing this misses is still pay history.
"""

import re

HISTORY_RE = re.compile(
    # "current base salary", "previous package", "existing OTE", "last comp"
    r"\b(current|previous|prior|past|last|existing|present|former)\s+(base\s+)?"
    r"(salary|pay|comp(ensation)?|wages?|package|ote|earnings|remuneration|rate)\b"
    # "salary history", "pay history"
    r"|\b(salary|pay|wage|compensation|comp)\s+history\b"
    # "per prior employer's package", "matches former employer pay"
    r"|\b(current|previous|prior|former|last)\s+employer'?s?\s+(package|pay|salary|comp\w*|rate|base|ote)\b"
    # "she earns 100k today", "what he makes now", "is paid 90k at the moment"
    r"|\b(earn|earns|earning|make|makes|making|paid|gets|getting)\b[^.;\n]{0,30}?"
    r"\b(now|today|currently|at\s+present|at\s+the\s+moment)\b"
    # "currently earns / makes / on 105"
    r"|\bcurrently\s+(earns|makes|making|paid|on|gets|getting)\b"
    # "he's on 105 base now"
    r"|\bon\s+[$€£]?\s?\d[\d,.]*\s?k?\s+(base\s+)?now\b",
    re.I)
