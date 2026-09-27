# Confidence, coding basis and the review split

## Contents
1. Confidence levels
2. Coding against the client's own chart
3. Ready to post vs Needs review
4. Reading from a connected ledger (optional)
5. Sheets delivery (optional)

## 1. Confidence levels

| Level | When | Example |
| --- | --- | --- |
| High | Evidence ties to the payment line and an approved written rule or account definition points to one approved account | Figma seat receipt, rule R1 → Software subscriptions |
| Medium | Purpose is clear but more than one account could fit; or the basis is history only, an unapproved rule, or a conflicting rule | Trainline: rule 4 splits client travel and training |
| Low / unresolved | Purpose, entity, split or support is missing; any special line | Amazon order with no receipt |

Caps from `propose_from_history.py` are ceilings: a rule proposal can be
lowered by the evidence, never raised above the cap.

## 2. Coding against the client's own chart

- Use the owner's exact account names. A generic taxonomy is not a chart of
  accounts. Category models struggle with per-company categories and description
  formats and start cold on a new client [59], so expect lower confidence in the
  first period and say so.
- Cite the account definition in each reason where one exists; short account
  definitions keep coding consistent [44].
- Class, location, job or fund come only from lists the owner supplied [6][12].
  Coding to the right job decides whether a contractor can tell which jobs make
  money [6]; never invent a dimension value.
- When the owner settles an item and says it should always go that way, add a
  row to `coding-rules.csv` with the approver and date and `status=approved`.
  A rule Mina suggests starts as `proposed` and caps at medium until approved.

## 3. Ready to post vs Needs review

QuickBooks' AI features also split lines into ones handled automatically and
ones left for review [57]. `write_review.py` applies the split:

- **Ready to post**: confidence high, evidence tied, account approved, no
  review need, no special line, not excluded. "Ready to post" means ready for
  the owner to post; Mina does not post.
- **Needs review**: everything else, each with the one fact or owner needed.

## 4. Reading from a connected ledger (optional)

If `intake.json` marks the ledger `live`:

1. `find_capability(query="<ledger> list accounts")` and
   `find_capability(query="<ledger> bank transactions for review")`.
2. `describe_capability(id=...)`: confirm each is a read. Do not call anything
   that categorises, matches, posts or updates.
3. `run_capability(id=..., input={...}, validate_only=true)`, then the real read.
4. Label the source `ledger API, <timestamp>`; include auto-added bank-rule
   items [100].
5. A sign-in card means stop and ask the user to connect; work from exports
   meanwhile.

Pushing categories back into the ledger is posting. This skill does not do it.

## 5. Sheets delivery (optional)

Only if the user asks for a Google Sheet and names the target sheet:
`find_capability(query="google sheets append rows")` → `describe_capability` →
`run_capability(..., validate_only=true)` → ask with `ask_question`: "Append
N rows to `<sheet name>`, tab `<tab>`?" → on yes, append only (never overwrite
or clear). The platform may also hold the call for approval
(`approval_required`); wait for the result.
