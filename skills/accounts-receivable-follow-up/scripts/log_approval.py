#!/usr/bin/env python3
"""Record an owner's approval against the exact artefact that was shown.

An approval covers one artefact (by SHA-256) and one named action. If the file
changed after it was shown, the approval is refused and a new one is needed.

    cd ~/skills/<slug>
    # 1. when showing the artefact for approval:
    python3 scripts/log_approval.py hash /home/user/out/draft-oriel.html
    # 2. after the owner's answer (pass the option label exactly as picked):
    python3 scripts/log_approval.py record --artefact /home/user/out/draft-oriel.html \
        --shown-sha <hash from step 1> --action "create draft oriel-2026-04 in Xero with status Draft" \
        --approver "Jo (as stated in chat)" \
        --option "Approve exactly as shown: create it in Xero as a Draft (status Draft only)" \
        --log ~/workspace/bookkeeping/<entity>/approvals.csv
    #    or, for a typed answer, --reply "<verbatim text>"
    # 3. before acting, confirm the approval still matches:
    python3 scripts/log_approval.py verify --artefact ... --action "..." --log ...

Which answers count as a yes (a closed list; everything else is refused):
- Option labels, matched exactly (case and spacing aside), each tied to the
  kind of action it allows:
    "Send exactly as shown"                       -> an action starting "send"
    "Approve exactly as shown: create it in <system> as a Draft (status Draft
     only)"                                       -> an action starting "create draft"
                                                     that names the same <system>
- A typed reply that is exactly one of: yes, approve, approved, go ahead,
  yes approve, yes go ahead (the action named in the question, except a
  "create draft" action), or send it, yes send it (send actions only).
  A "create draft" action needs the option label, or a typed reply that itself
  names creating and the system: "create it in <system>", "yes create it in
  <system> as a draft", "go ahead and create the draft in <system>". A bare
  "yes" to a question whose options include "I will number and issue it
  myself" is ambiguous, so it never approves creating a draft.
  Trailing punctuation is ignored. Anything longer or conditional ("yes but
  change the amount", "I don't approve", "please don't send it yet") is not a
  yes: ask again with the card.
- Never a yes: "I will send it myself", "Approve exactly as shown: I will
  number and issue it myself" (the owner acts; nothing is recorded for Mina to
  do), "Change it first", "Approve with the changes I type" (edit, re-render,
  re-hash, ask again), "Not yet", "No", or an empty reply.

`--approver` is who the user said approved; identity is never inferred.
Refuses (exit 1) when: the artefact hash differs from --shown-sha; the answer
is not a yes for this action; verify finds no matching approval or a later
edit. Exit 2 on bad input. Appends only; never edits rows. Only yes answers
are written, so every row in approvals.csv is an approval.
"""

import argparse
import csv
import hashlib
import os
import re
import sys
from datetime import datetime, timezone

FIELDS = ["timestamp", "artefact_path", "artefact_sha256", "action", "approver_as_stated", "verbatim_reply"]

# option label (normalised) -> action prefix it allows
APPROVING_OPTIONS = [
    (re.compile(r"^send exactly as shown$"), "send"),
    (re.compile(r"^approve exactly as shown: create it in (?P<system>[a-z0-9 .&'-]+) as a draft "
                r"\(status draft only\)$"), "create draft"),
    # typed replies that name creating and the system themselves
    (re.compile(r"^(?:(?:yes|ok|approved?|go ahead)(?: and| please)?\s+)?(?:please\s+)?create "
                r"(?:it|the draft|a draft|the invoice|this|draft)(?: as a draft)? in (?P<system>[a-z0-9.&'-]+"
                r"(?: [a-z0-9.&'-]+)?)(?: as a draft)?(?: \(status draft only\))?$"), "create draft"),
]
# typed replies (normalised) -> action prefix they allow ("" = any named action)
APPROVING_REPLIES = {"yes": "", "approve": "", "approved": "", "go ahead": "", "yes approve": "",
                     "yes go ahead": "", "send it": "send", "yes send it": "send"}
NEGATIONS = re.compile(r"\b(not|no|don't|dont|do not|never|hold|wait|change|changes|myself|but|"
                       r"reject|later|yet|edit)\b")


def normalise(text):
    t = " ".join((text or "").replace("’", "'").strip().lower().split())
    return t.rstrip(".!")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def approval_scope(answer):
    """Action prefix this answer approves ("" = the named action, unless it is a
    "create draft" action; "create draft in <system>" = a draft in that system
    only), or None when it is not an approval."""
    a = normalise(answer)
    if not a:
        return None
    for rx, prefix in APPROVING_OPTIONS:
        m = rx.match(a) or rx.match(a.replace(",", ""))
        if m:
            system = m.groupdict().get("system")
            if system and NEGATIONS.search(a.split(" in ", 1)[0]):
                return None
            return f"{prefix} in {system.strip()}" if system else prefix
    a = a.replace(",", "")
    if a in APPROVING_REPLIES and not NEGATIONS.search(a):
        return APPROVING_REPLIES[a]
    return None


def allows(scope, action):
    """Whether an answer of this scope approves this action."""
    act = normalise(action)
    if scope is None:
        return False
    if scope == "":
        return not act.startswith("create draft")
    if scope.startswith("create draft in "):
        system = scope[len("create draft in "):]
        return act.startswith("create draft") and f" in {system} " in f" {act} "
    return act.startswith(scope)


def is_approval(answer, action=""):
    return allows(approval_scope(answer), action)


def record(artefact, shown_sha, action, approver, reply, log):
    current = sha256(artefact)
    if current != shown_sha:
        return 1, f"REFUSED: {artefact} changed since it was shown (shown {shown_sha[:12]}, now {current[:12]}); show it again and ask again"
    if not action.strip() or not approver.strip():
        return 2, "action and approver are required"
    scope = approval_scope(reply)
    if scope is None:
        return 1, (f"NOT RECORDED as approval: '{reply}' is not a yes. The owner may act themselves, "
                   "wants changes, or has not agreed; do not act. Re-ask with the card if unclear")
    if not allows(scope, action):
        if scope == "":
            return 1, (f"NOT RECORDED as approval: a bare '{reply}' does not approve '{action}': the owner "
                       "may mean to issue it themselves. Ask again; only the option 'Approve exactly as "
                       "shown: create it in <system> as a Draft (status Draft only)' or a reply naming "
                       "create and the system approves creating a draft")
        return 1, f"NOT RECORDED as approval: '{reply}' approves a '{scope}' action, not '{action}'"
    new = not os.path.exists(log)
    os.makedirs(os.path.dirname(os.path.abspath(log)), exist_ok=True)
    with open(log, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "artefact_path": artefact, "artefact_sha256": current, "action": action,
                    "approver_as_stated": approver, "verbatim_reply": reply})
    return 0, f"approval recorded: {action} on {os.path.basename(artefact)} ({current[:12]})"


def verify(artefact, action, log):
    if not os.path.exists(log):
        return 1, "no approvals log"
    current = sha256(artefact)
    with open(log, encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["action"].strip() == action.strip()
                and os.path.basename(r["artefact_path"]) == os.path.basename(artefact)]
    if not rows:
        return 1, f"NO APPROVAL for action '{action}' on {os.path.basename(artefact)}"
    last = rows[-1]
    if last["artefact_sha256"] != current:
        return 1, "APPROVAL IS STALE: the artefact changed after approval; ask again"
    if not is_approval(last["verbatim_reply"], action):
        return 1, f"NO APPROVAL: the logged reply '{last['verbatim_reply']}' is not a yes for '{action}'"
    return 0, f"approved by {last['approver_as_stated']} at {last['timestamp']}: '{last['verbatim_reply']}'"


def selftest():
    import tempfile
    send = "send reminder-kestrel.html to accounts@kestrel.example"
    xero = "create draft oriel-2026-04 in Xero with status Draft"
    # every option on the AR card (evidence-and-sending.md section 2)
    assert is_approval("Send exactly as shown", send)
    for opt in ("I will send it myself", "Change it first", "Not yet"):
        assert not is_approval(opt, send), opt
    # every option on invoice Q4 (templates/approval-questions.md)
    assert is_approval("Approve exactly as shown: create it in Xero as a Draft (status Draft only)", xero)
    assert is_approval("Approve exactly as shown: create it in QuickBooks as a Draft (status Draft only)",
                       "create draft oriel-2026-04 in QuickBooks with status Draft")
    for opt in ("Approve exactly as shown: I will number and issue it myself",
                "Approve with the changes I type", "Not yet"):
        assert not is_approval(opt, xero), opt
    # an option only approves its own kind of action
    assert not is_approval("Send exactly as shown", xero)
    assert not is_approval("Approve exactly as shown: create it in Xero as a Draft (status Draft only)", send)
    # typed replies: exact yes only, no negation or condition
    for yes in ("yes", "Yes.", "approve", "Approved!", "go ahead", "Yes, go ahead"):
        assert is_approval(yes, send), yes
        # a bare yes to invoice Q4 could mean "I will issue it myself": never a create
        assert not is_approval(yes, xero), yes
    for yes in ("create it in Xero", "Yes, create it in Xero as a draft", "go ahead and create the draft in Xero"):
        assert is_approval(yes, xero), yes
        assert not is_approval(yes, send), yes
    assert not is_approval("create it in QuickBooks", xero), "the reply must name the same system"
    assert not is_approval("Approve exactly as shown: create it in QuickBooks as a Draft (status Draft only)", xero)
    assert not is_approval("don't create it in Xero", xero)
    assert is_approval("send it", send) and not is_approval("send it", xero)
    for no in ("I don't approve", "Please don't send it yet", "Yes but change the amount to 600 first",
               "no", "No, not yet", "do not send", "hold it", "wait", "", "   ", "yes send it myself",
               "approve with changes", "I will send it myself", "not approved", "never"):
        assert not is_approval(no, send), no
    with tempfile.TemporaryDirectory() as d:
        art = os.path.join(d, "draft.html")
        log = os.path.join(d, "approvals.csv")
        with open(art, "w") as fh:
            fh.write("draft v1")
        h = sha256(art)
        assert record(art, h, xero, "Jo", "Not yet", log)[0] == 1
        assert record(art, h, xero, "Jo", "yes", log)[0] == 1, "a bare yes never approves a Xero create"
        assert record(art, h, send, "Sam", "I will send it myself", log)[0] == 1
        assert not os.path.exists(log), "a refusal must not write a row"
        assert verify(art, send, log)[0] == 1
        assert record(art, h, xero, "Jo",
                      "Approve exactly as shown: create it in Xero as a Draft (status Draft only)", log)[0] == 0
        assert verify(art, xero, log)[0] == 0
        assert verify(art, send, log)[0] == 1, "approval covers one action only"
        with open(art, "w") as fh:
            fh.write("draft v2")
        assert verify(art, xero, log)[0] == 1
        assert record(art, h, xero, "Jo", "Approve", log)[0] == 1
        # a non-approval row written by an older script is not read as a yes
        h2 = sha256(art)
        with open(log, "a", encoding="utf-8", newline="") as fh:
            csv.DictWriter(fh, fieldnames=FIELDS).writerow(
                {"timestamp": "2026-05-01T00:00:00+00:00", "artefact_path": art, "artefact_sha256": h2,
                 "action": send, "approver_as_stated": "Sam", "verbatim_reply": "I will send it myself"})
        assert verify(art, send, log)[0] == 1
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["hash", "record", "verify", "selftest"], nargs="?")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--artefact")
    ap.add_argument("--shown-sha")
    ap.add_argument("--action", default="")
    ap.add_argument("--approver", default="")
    ap.add_argument("--option", default="", help="the option label exactly as the owner picked it")
    ap.add_argument("--reply", default="", help="the owner's typed reply, verbatim")
    ap.add_argument("--log")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or a.command == "selftest":
        return selftest()
    try:
        if a.command == "hash":
            print(sha256(a.path or a.artefact))
            return
        if not (a.artefact and a.log):
            print("error: --artefact and --log are required\nfix: see the usage at the top of this file", file=sys.stderr)
            sys.exit(2)
        if a.command == "record":
            if a.option and a.reply and normalise(a.option) != normalise(a.reply):
                print("error: pass either --option or --reply, not two different answers\n"
                      "fix: record the one answer the owner gave", file=sys.stderr)
                sys.exit(2)
            code, msg = record(a.artefact, a.shown_sha or "", a.action, a.approver, a.option or a.reply, a.log)
        else:
            code, msg = verify(a.artefact, a.action, a.log)
    except FileNotFoundError as e:
        print(f"error: {e}\nfix: check the artefact and log paths", file=sys.stderr)
        sys.exit(2)
    print(msg)
    sys.exit(code)


if __name__ == "__main__":
    main()
