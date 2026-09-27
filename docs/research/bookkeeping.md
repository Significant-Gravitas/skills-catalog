# Bookkeeper (small business): research dossier and improvement plan

Expert: **Mina** (`experts/mina.yml`), job title Bookkeeper.
Kit reviewed (every file read): `bookkeeping-getting-started`, `expense-categorization`,
`invoice-drafting-and-issue`, `accounts-receivable-follow-up`, `statement-reconciliation`
(+ `references/bank-rec-layout.md`), `month-end-close-checklist`
(+ `references/close-dependency-map.md`), `monthly-profit-and-loss-summary`,
`bookkeeping-exception-escalation`.
Inputs: six research files (jobs, standards, canon, modern, failure, tools) and the runtime
ground truth `capabilities.md` [104]. Written 2026-09-27.

Conventions. `[n]` points to section 8. Anything not backed by a source is labelled
*practitioner judgement (unsourced)*. "Job weight" counts come from a sample of 14 bookkeeper
postings fetched in September 2026 (plus three from April 2026) [1]; they describe that sample,
not the whole market.

Hard constraints this plan respects: no skill is renamed, deleted or split; slugs, frontmatter
`name` and existing `triggers` stay; no expert loses a capability named in its persona; every
guardrail change tightens. Nothing here touches `catalog.yml`, `release.json`, `experts/` or
`tools/`.

---

## 1. Role and what great looks like

A small-business bookkeeper keeps the transactional record complete, correctly coded and tied to
external evidence (bank, card, processor and lender statements), so that the owner can run the
business and the external accountant can close, adjust and file without first cleaning up.
Postings put reconciliation first (13 of 14), then payables and receivables/invoicing (11 of 14
each), month-end close (10 of 14) and financial reports (10 of 14) [1][2][3][5]. The work is often
part-time: 10 to 20 hours a week at about $25 to $30 an hour in the cited part-time postings
[16][1]; a full-time full-charge role lists $36.10 to $41.80 an hour [9][105].
Outsourced and multi-client roles expect the bookkeeper to own the whole cycle across many
entities [6][9][4].

What great looks like, as the sources describe it:

- **Zero unexplained discrepancies, on a cadence.** Scalesource's posting sets "zero unexplained
  discrepancies" and books closed "by day 10 or faster" [4]. A CPA practice guide puts a normal
  small-business close at 5 to 10 business days after month-end [66]. This matches the
  statement-reconciliation skill, which treats a reconciliation as complete only at zero
  unexplained difference; the persona (experts/mina.yml) also accepts every remaining item being
  owned with a next step.
- **Evidence behind every figure.** A balanced trial balance can still be wrong (wrong account,
  omitted or duplicated entries) [36]. A bank line proves payment, not that the cost was a business
  expense [18]. Great bookkeepers keep both kinds of evidence.
- **Coding that makes the books useful.** Coding to the right account *and* class, job or cost
  centre "decides whether a contractor can tell which jobs are making money" [6].
- **Clean handoff to the accountant and clear explanation to the owner.** Postings ask for records
  "kept ready for the owner, CPA, or finance lead" [4], coordination with external CPAs [6][7][5],
  and "explaining accounting to non-financial leaders" [1].
- **Controls in a business too small to segregate duties.** Where segregation is impractical,
  management selects and develops alternative control activities [41]. Management review of
  accounts is one of four controls associated with at least 50% lower fraud losses and duration
  [43]. That the owner is the reviewer in an owner-run business is practitioner judgement
  (unsourced).

The role is shifting from data entry to review. BLS projects a 6% fall in bookkeeping clerk jobs
from 2025 to 2035 because software automates entry [69], and the major ledgers now ship AI
categorisation and auto-reconciliation that only auto-handles high-confidence lines and leaves the
rest for people [54][57]. That puts the value in exactly what Mina's persona already does: a
review queue, control totals and owned exceptions.

## 2. Jobs to be done (weighted by postings)

Weights are the share of the 14 postings that name the duty, tallied in the research file
research-jobs.json [105] over postings [1]-[16]. The bracketed source in each row is an example
posting that names the duty, not the source of the count. "Covered by" names the kit skill that
handles it today.

| # | Job | Weight | Covered by |
|---|---|---|---|
| J1 | Reconcile bank, card, loan and processor accounts | 13/14 [1] | statement-reconciliation |
| J2 | Accounts payable: bill entry, vendor payments, payment runs | 11/14 [2] | **none** (gap) |
| J3 | Invoicing, billing and receivables | 11/14 [2] | invoice-drafting-and-issue, accounts-receivable-follow-up |
| J4 | Month-end close support or ownership | 10/14 [3] | month-end-close-checklist |
| J5 | Financial statements and reports (P&L, balance sheet, cash) | 10/14 [5] | monthly-profit-and-loss-summary (P&L only) |
| J6 | Transaction coding to account and class/job | 5/14 explicit [6]; implied by most | expense-categorization |
| J7 | Chase owners/clients for missing documents | 6/14 [10] | bookkeeping-exception-escalation (partly) |
| J8 | Collections and aging follow-up | 5/14 [15] | accounts-receivable-follow-up |
| J9 | Payroll processing or recording | 6/14 [8] | out of scope by persona; recording journal not covered |
| J10 | Journal entries, accruals, prepaids, fixed-asset schedules | 4/14 [7] | proposals only (month-end, escalation) |
| J11 | Hand-off to external CPA / tax preparer | 4/14 [4] | bookkeeping-exception-escalation |
| J12 | Sales tax, 1099/W-9 support | 3-4/14 [105]; sales tax e.g. [1][8][5], 1099 e.g. [7][6] | routed; no preparation skill |
| J13 | Cleanup and catch-up of historical books | 2/14 [9][1] | **none** (gap) |
| J14 | Intake and set-up of a new client/entity | implied by multi-client (6/14) [9] | bookkeeping-getting-started |

### J1 Reconcile an account (highest weight)
- **Trigger:** statement arrives; month-end; balance "doesn't match"; processor payout cannot be
  found against invoices.
- **Inputs:** statement (PDF or export) with opening and closing balance; ledger register for the
  same account and cutoff; prior period's approved reconciliation; for processors, the payout
  reconciliation or activity report [94][96].
- **Senior steps:** (1) confirm this period's opening balance equals last period's approved
  statement closing balance; if not, suspect an edited reconciled item [89][90]. (2) Check feed
  completeness against the real statement: feeds can lag (Amex may update only 2 to 3 times a
  week) and Xero's "statement balance" is the feed, not the bank [102][91]. (3) Match in passes,
  keyed where possible on institution + account + bank transaction ID (FITID) [93]. (4) Classify
  each reconciling item as bank-side timing or book-side correction; only book-side items need
  entries [35]. (5) For processor deposits, break each net payout into gross, fees, refunds and
  disputes using the payout report, treating the processor balance as a clearing account [94][5].
  (6) Report the unexplained difference; never plug it [51][50].
- **Output:** reconciliation schedule with both adjusted balances, item classes, aging of open
  items, owner per item.
- **Decisions:** what is timing vs error (bookkeeper proposes); any correcting entry (accountant
  or owner approves) [35][80].

### J2 Accounts payable (gap)
- **Trigger:** bill received; payment run due; supplier statement mismatch; bank-detail change.
- **Inputs:** bills, POs and receiving records where they exist, vendor master, payment calendar.
- **Senior steps:** two- or three-way match (bill vs PO vs receipt; skip for small recurring
  bills) [46]; duplicate-bill check; verify any bank-detail change through a known contact [61];
  never let vendor payments take priority over payroll tax deposits [75]; record how each
  contractor was paid: payments by card or through a third-party network that the settlement
  entity reports on 1099-K are excluded from 1099-NEC [24]; the accountant decides (personal-transfer
  rails may still need 1099-NEC; practitioner judgement, unsourced).
- **Output:** bill review queue and a proposed payment run for owner approval.
- **Decisions:** what to pay and when (owner); worker classification and 1099 status
  (accountant) [27].

### J3 Invoicing and receivables
- **Trigger:** billing date per contract or recurring schedule; work completed; customer query.
- **Inputs:** contract/SOW/PO, recurring billing schedule, tax fields from the accountant,
  invoice register, payments through cutoff.
- **Senior steps:** draft from contract terms and recurring schedule [14]; check the legally
  required fields for the jurisdiction [48][28]; keep sales tax as a liability, never revenue [77];
  in Xero keep the invoice in Draft until approval, because approval posts it and afterwards it can
  only be voided [103]; for AR, work from the aging detail and confirm terms first, because an
  invoice with no due date ages from its transaction date [97][98].
- **Output:** draft invoice with review block; aging table; staged reminder drafts; contact and
  dispute log.
- **Decisions:** pricing and terms (owner); late fees and statutory interest (owner, only where
  the jurisdiction is confirmed) [30][47]; bad-debt write-off (accountant) [38][98].

### J4 Month-end close
- **Trigger:** period end.
- **Inputs:** all Level 1 sources in the dependency map; prior open items; close calendar.
- **Senior steps:** cutoff; reconciliations; balance-sheet review; P&L variance review;
  adjustments with documentation; final review [66]. Finish invoicing, check for bills not yet
  received, then reconcile before reviewing the draft statements, which "nearly always" contain
  errors on the first pass [45]. Skip small accruals and standardise recurring ones [44]. Where
  duties cannot be segregated, management selects alternative control activities [41]; owner
  sign-off of the bank reconciliation is the proposed one (practitioner judgement, unsourced). The
  ledger admin sets the lock date [80].
- **Output:** close status report, open-items register carried forward, draft statements marked
  DRAFT.
- **Decisions:** adjustments, estimates and locking (accountant/owner).

### J5 Reporting
- **Trigger:** monthly close done or owner asks "why did profit change".
- **Inputs:** ledger P&L export with stated basis, comparison period, open items.
- **Senior steps:** print the basis (cash or accrual), period and currency on every figure;
  never compare figures on different bases [99][19][52]; keep cash movement apart from profit;
  explain the largest movements from source items; tailor to the reader [6].
- **Output:** draft P&L brief. Postings also expect balance sheet and cash views [5] (see gaps).

### J6 Coding transactions
- **Trigger:** new feed lines, receipts, card export.
- **Inputs:** export, receipts, chart of accounts with short account definitions [44], coding
  rules, class/location/job/fund lists [6][12][13]. Construction adds job costing and progress
  billing [6][11]; percentage-of-completion revenue is a policy call for the accountant [32].
- **Senior steps:** code against the client's own chart and history, not a generic taxonomy, and
  expect low confidence in the first period [59]; keep refunds, transfers, owner items, loan
  payments and sales tax out of operating expense [81][78][77]; require receipts that tie to a
  payment line [60]; check auto-posted items that skipped review [100].
- **Output:** review table, split into ready-to-post and needs-review [57].
- **Decisions:** deductibility, capitalisation, worker classification (accountant) [22][27].

### J7 Missing-documents chase
- **Trigger:** unresolved item that one document would settle.
- **Senior steps:** ask the smallest question; batch requests per owner; track them until
  answered [10].
- **Output:** a missing-documents request list (no template in the kit today).

### J8-J13
Collections (J8) is covered with J3. Payroll (J9), journal-entry schedules (J10), sales tax and
1099 preparation (J12) and cleanup (J13) are either outside the persona's boundaries or not
covered; section 7 lists them as gaps. CPA hand-off (J11) is the escalation skill's job.

### J14 Intake
- **Trigger:** new client, entity or period.
- **Senior steps:** record entity and period for every source so books for different clients
  never mix [9]; accept raw POS and bank exports, since some services book without a QBO or Xero
  file [10]; confirm where the system of record lives and that the owner holds exportable copies
  (Bench shut down on 27 December 2024 and cut customers off at once) [62][85]; for UK sole traders
  ask about Making Tax Digital status [31][67].

## 3. Knowledge to encode

### 3.1 Reconciliation
- Bank side: add deposits in transit, subtract outstanding checks, correct bank errors. Book side:
  add unrecorded income, subtract unrecorded fees/NSF, correct book errors. Only book-side items
  need entries. Done when adjusted balances are equal [35].
- A balanced trial balance does not prove correctness [36].
- Divide-by-nine: if a difference divides evenly by 9, suspect a transposition first [36].
- Dedupe key: institution + account + FITID; FITIDs are unique only within an account. Fall back
  to date + amount + description when FITIDs are missing or unreliable [93].
- QuickBooks Online: statuses R, C and blank; un-clearing changes next period's opening balance;
  undoing a reconciliation is irreversible and deletes reports [89]. A saved reconciliation report
  is a snapshot and does not prove the register still agrees [90].
- Xero: the summary reads "Balance in Xero - Outstanding Payments - Outstanding Receipts +
  Un-Reconciled Bank Statement Lines = Statement Balance" using Xero's signed figures, so
  outstanding payments show as negative numbers [91]. With all terms as positive magnitudes:
  statement balance = Balance in Xero + outstanding payments - outstanding receipts +/-
  unreconciled statement lines (a payment recorded in Xero but not yet cleared leaves Xero lower
  than the bank). The statement balance comes from the feed, so check it against the real
  statement [91]. Diagnose a gap month by month to find where it first appears [92].
- Duplicates in QBO come mostly from overlapping imports, reconnecting, double-connected
  accounts, or adding a feed line instead of matching it. A duplicate still in For Review is
  Excluded, not deleted, or it downloads again [79].
- Undeposited Funds: the account may be renamed, so identify it by Detail type = Undeposited
  Funds [88]. A lingering balance at month-end is an exception, and adding a feed deposit as new
  income while payments sit there double-counts revenue (practitioner judgement, unsourced;
  [88] does not cover this trap).
- Processors: Stripe payouts are net batches; use the Payout reconciliation report keyed on
  `automatic_payout_id`, which is set only for accounts on an automatic payout schedule; for
  manual payouts run the by-payout report with the payout ID [94]. The Balance summary does not link payouts to payments, and report
  time zone causes cutoff differences [95]. A payout `in_transit` at period end is timing, not
  missing [95]. PayPal activity rows have Gross, Fee, Net and Balance Impact (Debit, Credit or
  Memo); reports over 50,000 rows arrive split across several files in a ZIP, and the maximum
  range is 12 months per report [96]. That Memo rows do not move cash is an inference from the
  Balance Impact field, not stated in [96]. Clearing equation: gross sales −
  fees − refunds − chargebacks = net deposit [5][94].
- Petty cash is imprest: cash counted + receipts = fund amount; differences go to over/short and
  recurring shortages are a control flag [40].
- Opening balances post against Opening Balance Equity; a non-zero OBE balance is a set-up
  exception for the accountant [101].
- AI failure to design against: agents pulled unrelated transactions to make a bank balance tie
  [51]; errors compound month over month [50][51]; agents abandon a tool after 2-3 failures and
  cannot recover from wrong balances [71].

### 3.2 Evidence and coding (US-centred, with UK notes)
- Supporting documents per category (receipts, expenses, assets) are listed in Pub 583; proof of
  payment alone does not establish a deduction [18]. Statement fields that substitute for a
  cancelled check: amount, payee, posting/transaction date [18].
- Travel/meals/gifts: documentary evidence for all lodging and any other item of $75 or more;
  record amount, time, place and business purpose at or near the time [20][21]. Meals are
  generally 50% deductible, so keep them in their own account; deductibility stays with the
  accountant [21].
- Capitalisation: the de minimis safe harbor ($2,500 per item or invoice without an applicable
  financial statement, $5,000 with) needs an election and a policy in place at year start, and
  applies per item, so itemised invoices matter [22][83]. The bookkeeper flags; the accountant
  decides.
- Loan payments split into interest (expense) and principal (liability); without a lender
  schedule the line is unresolved [78].
- Commingled personal items belong in owner equity (contribution/draw), not the P&L; flag, don't
  categorise [81][18].
- Sales tax collected is a liability; a "sales tax expense" line in the P&L is an exception [77].
- 1099-K totals mix personal and business receipts; they are not revenue [82].
- AI-generated receipts were 70.8% of AppZen's flagged fake receipts by mid-May 2026: a receipt
  supports an expense only when it ties to a card or bank line [60].
- Coding against the client's own chart matters; ML categorisation struggles with description
  formats and per-company categories, with a cold-start problem [59]. Short account definitions
  keep coding consistent [44].
- QBO bank rules apply one rule per transaction in priority order, and auto-add posts without
  review [100].

### 3.3 Invoicing, receivables and payables
- UK invoice minimum fields: unique number, supplier details, customer name and address,
  description, supply date, invoice date, amounts, VAT if applicable, total; limited companies use
  the full registered name [48]. UK VAT invoices add VAT number, rate per line, VAT total in
  sterling, unit price, and more; VAT records kept at least 6 years [28].
- UK late payment: statutory interest 8% plus base rate for B2B; with no agreed terms, payment is
  late 30 days after either the customer gets the invoice or the goods or service are delivered
  (if this is later) (GOV.UK) [30]; fixed sums £40/£70/£100; a contract rate replaces the statutory one [30][47].
- AR aging: "Current" means not yet due; with no due date an invoice is due on receipt [97]. Work
  from the aging detail report [98]. Bad-debt estimate and write-off method belong to the
  accountant [38].
- AP matching: three-way match where POs exist; two-way against approved terms otherwise; skip for
  low-value recurring bills [46].
- US 1099: NEC/MISC threshold is $2,000 for payments after 31 December 2025 (was $600) [23][24];
  1099-K threshold is back to more than $20,000 and more than 200 transactions [26]; card and
  third-party network payments that the settlement entity reports on 1099-K are excluded from
  1099-NEC [24] (record the payment method and let the accountant decide; personal-transfer rails
  may still need 1099-NEC, practitioner judgement, unsourced); 24% backup withholding
  applies when a payee has no correct TIN [25]. Stale $600 figures are a likely AI error [76].
  The bookkeeper produces payee totals and W-9 gaps; the accountant decides.

### 3.4 Close and reporting
- Four adjustment types (prepaid, unearned, accrued revenue, accrued expense); adjusting entries
  never involve cash; a cash-basis bank export cannot produce an accrual P&L by itself [37].
- Cash vs accrual definitions [19]; QBO reports default to the company method but can be switched
  per report, so every P&L must state its basis [99]. Calendar vs fiscal year: never assume
  calendar [19].
- Close sequence and 5-10 day target [66]; the first draft nearly always has errors [45].
- Lock the period after reconciling; only a primary/company admin can; edits after lock need a
  warning or password [80]. Fix closed-period errors in the current period, via the accountant
  (practitioner judgement, unsourced; [80] covers only the lock mechanics).
- Materiality is not a percentage alone; qualitative factors (flips loss to profit, covenants,
  owner pay, possible illegality) make small items material [33]; related parties are added as
  practitioner judgement (unsourced; not among SAB 99's listed factors).
- The hardest agent task is schedules and accruals; agents fetch the right documents and then
  substitute the wrong basis [52].

### 3.5 Controls and fraud
- Segregation of duties [39]; "where segregation of duties is not practical, management selects
  and develops alternative control activities" [41], and management review is one of the
  controls ACFE links to lower losses [43]. GrowthForce's small-business fallback is to consider
  an outsourced provider to manage the books [74]. That an AI which both codes and reconciles is
  itself a segregation gap, so owner sign-off matters, is practitioner judgement (unsourced).
- Small businesses had the highest median occupational-fraud loss in ACFE 2020 ($150,000), with
  check/payment tampering nearly 4x as common as in larger organisations [42]. ACFE 2026: median
  loss $104,000, median 12 months to detection, more than half involve missing or overridden
  controls, owner/executive frauds cost more than nine times employee frauds [73].
- BEC: $55.5 billion exposed losses 2013-2023; verify account-change requests through a second
  channel [61].
- Payroll trust-fund taxes: a person with authority to decide which creditors get paid can be
  personally liable; paying other creditors ahead of payroll tax indicates willfulness [75].
- Worker classification turns on behavioural control, financial control and relationship; the
  label on the contract does not decide it [27].

### 3.6 Retention and jurisdictions
- US retention: 3 years default; 4 years employment tax; 6 years if income under-reported by
  more than 25%; 7 years for bad debt/worthless securities; indefinitely if no return or fraud [17].
  Never recommend discarding records [17][84].
- UK retention: companies 6 years from the end of the financial year; sole traders at least 5
  years after the 31 January deadline [29].
- UK MTD for Income Tax: mandatory from 6 April 2026 above £50,000 qualifying income, £30,000
  from April 2027, £20,000 from April 2028; digital records and quarterly updates [31][67].
- US economic nexus for sales tax (post-Wayfair) can arise without physical presence; surface
  per-state totals, never say no tax is owed [86].
- Revenue recognition (IFRS 15 / ASC 606 five steps) is policy for the accountant [32].

## 4. Artefacts and their expected structure

| Artefact | Expected structure | Source / owner skill |
|---|---|---|
| Intake sheet | entity, period, currency, basis (or "open"), chart owner, source list (file, dates, export time, rows, currency, control total), approvers, accountant, system of record and export copies, dimensions used, jurisdiction flags (MTD, VAT) | getting-started; [9][62][31] |
| Expense review table | source+row, txn date, posting date, vendor, amount+currency, evidence, payment-line link, proposed account, class/location/job/fund, reason citing account definition, confidence, review need; footer totals | expense-categorization; [6][44][60] |
| Ready-to-post vs needs-review split | two lists; each item labels how it was treated | expense-categorization; [57] |
| Draft invoice + review block | number or "to be assigned", parties, reference, lines with period/qty/rate/total/source, subtotal, tax (supplied only), total, currency, due date, payment details, jurisdiction field check, status (Draft) | invoice-drafting; [48][28][103] |
| AR aging table | per open invoice: number, customer, issue date, due date/terms, original, credits, payments, open balance, days past due, bucket, group, dispute, promised date | AR follow-up; [97][98][38] |
| Reminder draft + contact log | staged draft; log row with stage, evidence cutoff, owner, approval state, next review | AR follow-up |
| Bank reconciliation schedule | statement side, ledger side, both adjusted balances, unexplained difference; classified items; aging of open items | statement-reconciliation; [35] |
| Processor clearing reconciliation | per payout: gross, fees, refunds, disputes, net, payout status, bank trace ID; tie to bank deposit and to revenue | statement-reconciliation; [94][95][96] |
| Close status report | per control: status, evidence, blocker, owner; control totals; proposed adjustments; checks not performed; open items carried | month-end; [66] |
| Draft P&L brief | header (entity, period, basis, currency, source, export date, comparison); table; 3-5 sourced points; exclusions; DRAFT label | P&L summary; [99][45] |
| Exception evidence pack | class, identifiers, facts, mismatch, amount, work done, deadline, one decision request, owner, interim state | escalation |
| Missing-documents request | per owner: item, why needed, what document settles it, due date | escalation (new asset); [10] |
| CPA hand-off pack | open items, proposed adjustments with support, payee totals/W-9 gaps, fixed-asset flags, accrual candidates | escalation (new asset); [4][7] |

Spreadsheets are the common exchange format (Excel named in 9/14 postings) [7]; tabular
artefacts should also be deliverable as CSV.

## 5. Tools, data and traps

### 5.1 Tools the market uses
- Ledgers: QuickBooks (10/14; QBO named in 6) and Xero (4/14) [5][6]. Yardi in property
  [3][13]. Some services book straight from POS and bank feeds [10].
- Commerce and payments: Shopify, Amazon, WooCommerce, Stripe, PayPal; payroll Gusto; spend Brex
  [5].
- Spreadsheets: Excel with pivots and lookups; Google Sheets [7][5].

### 5.2 What the runtime can actually do [104]
- A skill package may hold `references/`, `assets/` and `scripts/` beside SKILL.md (max 100
  files, 2 MiB each, 20 MiB total, no dotfiles, no spaces, depth ≤ 8). `scripts/` files are made
  executable and run with `bash_exec`, which starts in `/home/user`, so every command must be
  written `cd ~/skills/<slug> && python3 scripts/...`. Python availability is **unverified**;
  bodies must pre-flight (`python3 --version`) and fall back to working in the table by hand.
- User files come in with `read_workspace_file(..., save_to_path="/home/user/...")`; deliverables
  go out with `write_workspace_file(source_path=...)` and a `workspace://` link.
- Missing parameters: `ask_question` (up to 10 questions with options).
- Integrations (QBO, Xero, Gmail, Sheets) are reachable only through
  `find_capability` → `describe_capability` → `run_capability`, never from scripts; the sandbox
  holds only GitHub credentials. Deferred tools must be written `run_capability(id="tool:...")`.
  An unconnected integration returns a sign-in card: stop and ask.
- External writes (MCP writes, chat posts, `browser_act`) ask under the approval gate; the gate is
  active only in interactive sessions with the auto-mode flag, so the skills' own owner-approval
  rules must remain in the body regardless.
- `memory_search` can recall coding rules and account definitions when memory is on.
  `schedule_routine` exists for recurring runs (e.g. a monthly close reminder), but Mina has no
  routines today and this plan does not add any.
- Only `name`, `description`, `triggers` (≤ 10, ≤ 64 chars each) and body reach the model;
  critical rules must live in the body.

### 5.3 Data traps
| Trap | Effect | Guard |
|---|---|---|
| Feed lag (Amex 2-3 times a week) [102] | Empty feed read as "no activity" | Compare feed to statement before cutoff |
| Xero statement balance = feed [91] | Reconciles to a wrong "statement" | Tie to the real statement closing balance |
| Saved QBO rec report is a snapshot [90] | Old zero difference hides later edits | Rebuild the cleared balance; check opening = prior closing |
| Overlapping imports / double connections [79] | Doubled income/expense | FITID key, import-range check |
| Deleting feed duplicates [79] | Line downloads again | Recommend Exclude, owner performs it |
| Undeposited Funds, possibly renamed; find by Detail type [88] | Double-counted revenue (practitioner judgement, unsourced) | Flag month-end balance |
| Net processor payouts [94] | Deposits never match invoices | Clearing-account breakdown |
| Report time zone / `available_on` vs `created` [95] | Cutoff differences | State the time zone and date field |
| PayPal Memo rows (Balance Impact field [96]) | Non-cash rows counted as cash (inference from the field) | Filter on Balance Impact |
| No due date on invoice [97] | False "overdue" | Confirm terms first |
| Cash vs accrual switch per report [99] | Apples-to-oranges comparisons | Print basis; refuse cross-basis comparisons |
| Bank rules auto-add [100] | Items skip review | Include auto-added items in review |
| OBE balance [101] | Hidden set-up error | Flag to accountant |
| QBO CSV import limits (3 or 4 columns, one date format, 350 KB, 1,000 lines) [87] | Failed or garbled import | Validate before hand-off, if the owner asks for an import file |
| Stale thresholds ($600 1099) [76][23] | Wrong 1099 list | Never hard-code; state tax year; route |

## 6. Guardrails and where AI fails

### 6.1 Evidence of AI failure in this domain
- **Plugging reconciliations.** GIGAZINE reports that in AccountingBench the models would cheat
  by pulling unrelated transactions to make balances tie [51].
- **Compounding error.** First-month results were within about 1% of a CPA, later months diverged
  by over 15% [50]; accuracy fell from above 95% to below 85% over a year [51].
- **Giving up on tools and data.** Agents abandon a tool after 2-3 failures and cannot recover
  once balances are wrong [71].
- **Wrong basis.** On APEX-Accounting the best model reached 21.5% Pass@8 and none above 2.6%
  Pass^8; agents retrieve the right documents then substitute the wrong basis [52].
- **Hallucinated figures.** FinanceBench: GPT-4-Turbo with retrieval was wrong or refused on 81%
  of sampled questions [72].
- **Vendor accuracy claims need their caveats.** Digits' 98% figure came from a test set with
  fewer edge cases than real books [53].
- **Confident prose over uncertain numbers** and automation bias [63]; "a failure mode that looks
  like success" [64].
- **Tax answers from memory** are unreliable and rules change (OBBBA) [65][76].

### 6.2 Guardrails the kit already has (keep all)
No invented figures; no tax or accounting policy choices; no posting, issuing, sending, contacting
or moving money without explicit approval; route tax, payroll, equity, fraud and material items;
reconciliation complete only at zero unexplained difference (the statement-reconciliation skill's
rule; the persona also accepts every remaining item owned with a next step); drafts never
presented as final.

### 6.3 Guardrails to add (each tightens)
1. **No plugging, ever.** A match needs a one-to-one source link on both sides; never pull a
   transaction from another period, account or entity to close a gap [51][35]. (all reconciling
   skills)
2. **Period chaining.** Do not start period N unless period N−1's closing balances are approved
   or the gap is carried as a named open item; opening must equal the prior approved closing
   [50][89]. (reconciliation, close, P&L)
3. **Stop on source failure.** If a file or tool fails twice, stop and report the gap instead of
   continuing on partial data [71]. (all)
4. **Basis beside every figure.** Period, basis and currency on every computed number; never
   compare across bases [52][99]. (P&L, close)
5. **Receipt must tie to payment.** A receipt without a matching card/bank line is an exception,
   not support [60]. (expense)
6. **Bank-detail changes are always exceptions** needing out-of-band verification by the owner;
   never draft a payment to new details from email alone [61]. (escalation, and any AP work)
7. **Payroll tax first.** Never suggest ordering payments ahead of payroll tax deposits; escalate
   any shortfall at once [75]. (escalation, close)
8. **No thresholds from memory.** Quote a tax or reporting threshold only from a supplied or
   fetched current source, with its tax year; otherwise route [65][76]. (expense, escalation)
9. **Closed periods stay closed.** Never propose editing a locked or reconciled-period entry;
   propose a current-period correction for the accountant (practitioner judgement, unsourced);
   never undo a reconciliation [89]; lock mechanics [80].
   (reconciliation, close)
10. **Qualitative materiality.** Route items touching covenants, owner pay, possible illegality,
    or that flip profit to loss, whatever their size [33]; also related parties (practitioner
    judgement, unsourced). (escalation, P&L)
11. **Owner-delegate path.** If the concern involves the person who normally approves, route to
    the next named owner [73]. (escalation)
12. **Data minimisation to the model.** State what data the task needs and do not ask for more;
    no pasting of unrelated client data [63]. (getting-started)

## 7. Per-skill gap analysis and plan

Shared rules for every change below:
- Keep `name`, slug and all existing `triggers`; do not shorten descriptions. Where a trigger is
  proposed, it is additive and stays within 10 entries.
- Every new file is referenced from SKILL.md by relative path and read with
  `read_file ~/skills/<slug>/references/<file>` (or `read_workspace_file` fallback) [104].
- Every script is optional acceleration: SKILL.md says how to do the same check by hand if
  `python3` is missing, prints actionable errors, and never writes to a ledger or sends anything.
- Keep each SKILL.md body well under 500 lines; push tables to `references/`.

### 7.1 bookkeeping-getting-started
**Gaps.** No system-of-record/export check [62][85]; no dimensions (class, location, job, fund,
property) [6][12][13]; no multi-entity separation rule beyond "don't merge" [9]; no
source-document checklist by category [18]; no jurisdiction flags (MTD, VAT registration) [31];
no guidance to accept raw POS/bank exports [10]; no data-minimisation statement [63]; no
record-retention stance [17][29].

**Add to SKILL.md.**
- Intake items 9-12: where the ledger and documents live and whether the owner holds exported
  copies; dimensions in use; jurisdiction flags (US/UK, VAT-registered, MTD status for UK sole
  traders, fiscal year end); coding rules and short account definitions if any [44].
- "Accept raw POS, bank and processor exports; do not assume a QBO or Xero file exists" [10].
- Collect blocking gaps with `ask_question` (one question per gap, with options) [104].
- "Never advise discarding or deleting source records; retention questions go to the
  accountant" [17][29].
- A pre-flight line on what data the model will see and why [63].

**Create.**
- `references/source-document-checklist.md`: documents by category (receipts, purchases,
  expenses, assets, payroll) from Pub 583 [18], with proof-of-payment vs proof-of-cost [18].
- `references/jurisdiction-flags.md`: US vs UK intake questions, retention periods [17][29], MTD
  thresholds and dates [31][67], VAT record-keeping [28]; each dated, with "check the current
  source" wording.
- `assets/intake-sheet.csv` (or `.md` table): the intake columns above.
- `scripts/profile_sources.py`: for each CSV export, print row count, date range, date formats
  found, currencies, sum of amounts, duplicate FITID or (date, amount, description) keys [93].
  Run: `cd ~/skills/bookkeeping-getting-started && python3 scripts/profile_sources.py
  /home/user/<file>.csv`.

### 7.2 expense-categorization
**Gaps.** No class/job/fund columns [6][12]; no ready-to-post vs needs-review split [57]; no
payment-line link for receipts [60]; no US substantiation flags (threshold, lodging, meals
separate) [20][21]; no explicit handling for loan splits [78], sales tax [77], commingled items [81],
possible fixed assets with itemisation [22][83], contractor payments and payment method [24][27];
no check of auto-posted items [100]; no cold-start note [59].

**Add to SKILL.md.**
- Columns: `Class/location/job/fund` (only from supplied lists) and `Payment line` (row id of the
  matching card/bank line, or `none`).
- Output split: "Ready to post (high confidence, evidence tied)" and "Needs review"; the persona's
  "seven ready to post, three need review" pattern [57].
- Checks: receipt with no payment line → exception [60]; travel/meal/gift items at or above the
  substantiation threshold in references/substantiation-us.md (dated; confirm with the
  accountant), or any lodging, without a receipt → ask for purpose and attendees (US; do not
  decide deductibility) [20][21]; no dollar figure in the SKILL.md body (guardrail 8); loan payments without a lender schedule → unresolved [78]; sales tax lines kept out of
  expense [77]; personal-looking items → owner question [81]; equipment purchases → "possible fixed
  asset, accountant to decide", request itemised invoice [22][83]; recurring fixed payments to a
  "contractor" → classification flag for the accountant [27]; record payment method for
  contractor payees [24]; include auto-added bank-rule items in the review [100].
- "First period with a client: expect lower confidence; cite the account definition in each
  reason" [59][44].
- Guardrail 8 (no thresholds from memory).

**Create.**
- `references/special-lines.md`: loan, owner, transfer, sales tax, refund/reversal, fixed-asset,
  contractor and processor-fee handling, each with the question to ask and the owner [78][81][77]
  [22][27][96].
- `references/substantiation-us.md`: Pub 583 evidence rules [18], 26 CFR 1.274-5 [20], Pub 463
  meals [21], AI-receipt risk [60]; the only place in the skill package where the $75 figure appears, citing 26 CFR
  1.274-5(c)(2)(iii) [20]; dated, "confirm current rules with the accountant".
- `assets/expense-review-template.csv`: the column set.
- `scripts/expense_checks.py`: totals, exact and likely duplicates, receipts without payment lines,
  configurable substantiation threshold flag (default off; the owner supplies the value), rows
  excluded. Prints a summary and a CSV; never edits input.

### 7.3 invoice-drafting-and-issue
**Gaps.** No jurisdiction field checklist [48][28]; no sales-tax-as-liability note [77]; no
recurring-billing schedule check [14]; no ledger-status note (Xero Draft → Authorised posts)
[103]; no deterministic totals check.

**Add to SKILL.md.**
- "Check the draft against the field list for the seller's jurisdiction; block approval if a
  required field is missing" (reference) [48][28].
- "Tax on an invoice is a liability, not revenue; show it separately and only as supplied" [77].
- "For recurring billing, compare the draft to the schedule and the previous invoice; list any
  change" [14].
- "If the owner asks for the draft to be created in the ledger, it stays in Draft status;
  approval posts it and afterwards it can only be voided" [103]. Creating a ledger draft is a
  write via `run_capability` and needs the owner's yes for that action.
- Add "credit note" and "cross-border" to the existing routing list (already partly there).

**Create.**
- `references/invoice-field-checklists.md`: UK general minimum [48]; UK VAT invoice fields and
  6-year retention [28]; a US note that required fields are set by contract and state rules,
  labelled *practitioner judgement (unsourced)*.
- `assets/invoice-draft-template.md`: the draft plus review block.
- `scripts/invoice_totals.py`: recompute line totals, subtotal, supplied discount and tax, grand
  total; report rounding differences.

### 7.4 accounts-receivable-follow-up
**Gaps.** Aging buckets not specified [38][98]; QBO due-date semantics [97]; no dispute log
field [14]; UK statutory rights handling unspecified [30][47]; no link from AR to deposits in
Undeposited Funds [88].

**Add to SKILL.md.**
- Aging table with Current / 1-30 / 31-60 / 61-90 / 90+ by days past the due date, escalating the
  oldest bucket first; buckets confirmed with the owner [38][98].
- "A ledger shows an invoice with no due date as due on receipt; confirm terms before calling it
  overdue" [97].
- "Before chasing, check for payments sitting in Undeposited Funds or unapplied credits" [88].
- Dispute log columns: stated issue, date, evidence, owner, status [14].
- "Mention statutory interest or fixed recovery sums only if the owner opts in and confirms UK
  B2B and no contract rate" [30][47].
- Sending: "find the mail tool with `find_capability`, confirm with `describe_capability`, and
  call `run_capability` only after the owner's yes for that message" [104] (tightens the existing
  "connected mail tool" line).
- Bad-debt write-off is an accountant decision [38].

**Create.**
- `references/aging-and-terms.md`: bucket definitions and ledger semantics [97][98][38].
- `references/uk-late-payment.md`: statutory rate formula, fixed sums, contract override, daily
  interest example [30][47], dated.
- `assets/reminder-stages.md`: first reminder, second reminder, statement of account, and
  dispute acknowledgement; no threats; placeholders only.
- `scripts/ar_aging.py`: from an invoice/payment export plus cutoff, compute open balance, days
  past due, bucket; mark `status unconfirmed` where due date is missing.

### 7.5 statement-reconciliation (highest job weight)
**Gaps.** Bank-centric; postings require card, loan, processor and balance-sheet accounts [1][5];
no period-chaining check [50][89]; no feed-vs-statement check [91][102]; no FITID key [93]; no
ledger-specific diagnostics [89][90][91][92][79]; no processor clearing method [94][95][96]; no
petty cash [40]; no divide-by-nine hint [36]; no explicit anti-plug rule [51].

**Add to SKILL.md.**
- Pre-checks: opening equals prior approved closing (else suspect edited reconciled item, do not
  undo anything) [89][90]; feed complete against the real statement [91][102].
- Match key order: institution + account + FITID, then date + amount + reference [93].
- Guardrail 1 (no plugging) verbatim [51]; guardrail 3 (stop on source failure) [71].
- Account types: bank, card, loan (lender statement principal vs ledger liability) [78],
  processor clearing [94], petty cash imprest [40]; pick the equation from the reference.
- Diagnostics for an unexplained difference: divide-by-nine [36]; month-by-month search for when
  the gap first appears [92]; duplicate causes [79]; Undeposited Funds [88].
- Recommended fixes name the correct action for where a duplicate sits (Exclude in For Review,
  never delete) and are performed by the owner [79].

**Create.**
- `references/processor-clearing.md`: Stripe payout reconciliation columns, payout statuses,
  time-zone cutoff; `automatic_payout_id` is set only for automatic payouts, so for manual payouts
  run the by-payout report with the payout ID [94]; PayPal Gross/Fee/Net/Balance Impact and
  export limits (split ZIP over 50,000 rows, 12 months per report); the clearing equation
  [94][95][96][5].
- `references/ledger-diagnostics.md`: QBO R/C/blank, snapshot reports, undo warning, duplicates,
  Undeposited Funds, OBE; Xero summary equation and variance causes [89][90][79][88][101][91][92].
  Quote [91]'s signed form and the magnitude form side by side, with a worked example (Xero
  balance 10,000; outstanding payment 500; outstanding receipt 200; no unreconciled lines;
  statement balance = 10,000 + 500 - 200 = 10,300), so `rec_match.py` cannot hard-code the wrong
  sign.
- `references/account-types.md`: card, loan, petty cash, clearing, other balance-sheet
  statements; what "statement" means for each [40][78][35].
- Extend `references/bank-rec-layout.md` (keep all existing content): add a "prior-period tie"
  line above the layout and the anti-plug rule under "Unexplained difference".
- `scripts/rec_match.py`: exact and windowed matching passes, duplicate detection by FITID or
  composite key, both adjusted balances, unexplained difference, divide-by-nine hint, unmatched
  lists. It never produces a balancing entry. Input: statement CSV, ledger CSV, balances.
- `scripts/payout_breakdown.py`: from a Stripe payout reconciliation CSV or PayPal activity CSV,
  sum gross, fee, refund, dispute and net per payout and list payouts not `paid` at cutoff. Keys on
  `automatic_payout_id` for automatic payouts only; manual payouts need the by-payout report with
  the payout ID, so rows with an empty key are reported, never dropped [94].

### 7.6 month-end-close-checklist
**Gaps.** No close calendar [66]; controls lack processor clearing, Undeposited Funds, OBE and
bills-not-yet-received checks [88][101][45]; no owner sign-off of the bank rec as the alternative
control where duties cannot be segregated [41][43] (owner as reviewer: practitioner judgement,
unsourced); no lock-date step [80]; no prior-period tie [50]; no small-accrual guidance [44].

**Add to SKILL.md.**
- Default calendar (confirm with owner): cutoff days 1-2; reconciliations 2-4; balance sheet
  review 4-5; P&L variance 5-6; adjustments 6-7; final review 7-10 [66].
- Controls 10-14: processor clearing reconciled [94]; Undeposited Funds and suspense at zero or
  explained [88]; OBE zero or routed [101]; bills-not-yet-received check [45]; owner sign-off on
  each bank rec recorded (alternative control activity [41]; management review [43]; owner as
  signer is practitioner judgement, unsourced).
- "Close starts only when the prior period's closing balances are approved, or carried as an
  open item" [50].
- "Locking the period is the ledger admin's step; record the lock date the owner supplies; never
  bypass or ask to bypass it" [80].
- "Accrual candidates below the owner's stated threshold may be listed, not proposed" [44];
  qualitative materiality still applies [33].

**Create.**
- `references/close-calendar.md`: the day-by-day skeleton [66] and Bragg's sequence [45].
- Extend `references/close-dependency-map.md` (keep all existing content): Level 1 add processor
  reports; Level 2 add processor clearing and Undeposited Funds review; Level 5 add owner sign-off
  and lock date.
- `assets/close-status-template.csv`: control, status, evidence, blocker, owner, date.

### 7.7 monthly-profit-and-loss-summary
**Gaps.** No explicit cross-basis refusal [99]; accrual limits of cash data [37]; sales tax and
1099-K traps [77][82]; dimension views [6][12]; always-DRAFT rule is present, first-draft review
pass is not [45]; qualitative materiality [33]; cash view expected by postings [5].

**Add to SKILL.md.**
- "Print basis beside the table; if the comparison period's basis differs or is unknown, do not
  compute changes" [99][52].
- "A P&L built from bank data alone is cash-basis; list prepaid, deposit, unbilled and
  unreceived-bill candidates for the accountant" [37].
- Exceptions: any "sales tax expense" line [77]; revenue taken from a 1099-K total [82]; owner
  items in the P&L [81].
- Optional views by class/job/fund/property when the chart supports them [6][12][13].
- Optional "cash movement bridge" after the P&L, only from reconciled bank totals, clearly
  separate from profit (the body already says to keep cash apart) [5].
- "Review pass before release: re-add totals, check each large movement against a source" [45].

**Create.**
- `references/basis-and-comparability.md`: cash vs accrual definitions [19], QBO per-report
  method [99], four adjustment types [37], qualitative materiality [33].
- `scripts/pl_variance.py`: from two P&L exports, check detail sums to totals, compute changes,
  suppress percentages on zero or near-zero bases, list unmapped accounts.

### 7.8 bookkeeping-exception-escalation
**Gaps.** No missing-documents request (6/14 postings) [10]; no CPA hand-off pack [4][7]; no
payroll trust-fund rule [75]; no worker-classification class [27]; no AI-receipt class [60]; no
qualitative materiality triggers [33]; no owner-delegate path [73]; no 1099/W-9 gap class
[24][25].

**Add to SKILL.md.**
- New classes: payroll tax shortfall (raise at once) [75]; worker classification question [27];
  receipt with no payment line / possible generated receipt [60]; payee missing W-9/TIN (do not
  compute withholding) [25]; closed-period change detected [80][90].
- Qualitative triggers that escalate regardless of size [33].
- Owner-delegate path [73].
- Two output modes that reuse the pack: "missing-documents request" (batched per owner) and
  "accountant hand-off pack" (period-end list). Both remain drafts; sending follows the existing
  "send only after the owner says yes to that recipient" rule.

**Create.**
- `references/routing-matrix.md`: class → owner → urgency → safe interim state, drawing on
  [61][75][27][33][73].
- `references/red-flags.md`: BEC signals and out-of-band verification [61]; generated receipts
  [60]; fraud base rates and detection lag [42][73]; payroll trust-fund liability [75].
- `assets/missing-documents-request.md` and `assets/accountant-handoff-pack.md` templates.

### 7.9 Capabilities the role needs that no skill covers
- **Accounts payable and payment-run preparation** (11/14 postings) [2][46][61][75]: gap:
  consider a new skill.
- **Books cleanup and catch-up, oldest period first** [9][1][50]: gap: consider a new skill.
- **Balance-sheet view and balance-sheet account schedules** (prepaids, accruals, fixed-asset
  register, loan amortisation) [5][7][37]: gap: consider a new skill.
- **Payroll journal recording from a provider's register** (recording only; runs and filings
  stay out) [8][7]: gap: consider a new skill.
- **Year-end 1099/W-9 payee list and CPA year-end package** [24][25][4]: gap: consider a new
  skill.
- **Sales tax/VAT summary by jurisdiction for the adviser** (preparation only) [1][5][86]: gap:
  consider a new skill.
- **Ledger import-file preparation** (e.g. QBO CSV) [87]: gap: consider a new skill.

## 8. Sources

Type and era as recorded in the research files. "n.d." means the page shows no year.

| n | Source | URL | Year | Type | Era |
|---|---|---|---|---|---|
| 1 | Robert Half, Bookkeeper (Part-Time), Las Vegas NV | https://www.roberthalf.com/us/en/job/las-vegas-nevada/bookkeeper/03100-0013506289-usen | 2026 | job posting | current |
| 2 | Robert Half, Bookkeeper, Edison NJ | https://www.roberthalf.com/us/en/job/edison-new-jersey/bookkeeper/02760-0013510571-usen | 2026 | job posting | current |
| 3 | Robert Half, Bookkeeper, White Plains NY (real estate) | https://www.roberthalf.com/us/en/job/white-plains-new-york/bookkeeper/02970-0013501744-usen | 2026 | job posting | current |
| 4 | Scalesource, Bookkeeper & Accounting Support Specialist (Multi-Client) | https://apply.workable.com/scalesource-1/j/C86875D283 | 2026 | job posting | current |
| 5 | Catch Creation, Bookkeeper (Ecommerce) | https://job-boards.greenhouse.io/catchcreationllc/jobs/4078182009 | 2026 | job posting | current |
| 6 | Remote Raven, Full Charge Bookkeeper (CPA) | https://apply.workable.com/remote-raven/j/70CA2FAF85 | 2026 | job posting | current |
| 7 | Robert Half, Bookkeeper/Staff Accountant, Brookfield WI | https://www.roberthalf.com/us/en/job/brookfield-wisconsin/bookkeeperstaff-accountant/01300-0013476948-usen | 2026 | job posting | current |
| 8 | Robert Half, Bookkeeper, Red Bank NJ (CPA firm) | https://www.roberthalf.com/us/en/job/red-bank-new-jersey/bookkeeper/02660-0013481689-usen | 2026 | job posting | current |
| 9 | Robert Half, Full Charge Bookkeeper, Las Vegas NV | https://www.roberthalf.com/us/en/job/las-vegas-nevada/full-charge-bookkeeper/03100-0013514667-usen | 2026 | job posting | current |
| 10 | Rockstar, Bookkeeper (small-business bookkeeping service) | https://apply.workable.com/rockstar-3/j/A80A350C02 | 2026 | job posting | current |
| 11 | Robert Half, Bookkeeper/Office Administrator, Mahwah NJ (construction) | https://www.roberthalf.com/us/en/job/mahwah-new-jersey/bookkeeperoffice-administrator/02720-0013490059-usen | 2026 | job posting | current |
| 12 | Robert Half, Bookkeeper, Truckee CA (nonprofit) | https://www.roberthalf.com/us/en/job/truckee-california/bookkeeper/03110-0013507365-usen | 2026 | job posting | current |
| 13 | Robert Half, Bookkeeper jobs in New York NY (list page) | https://www.roberthalf.com/us/en/jobs/new-york-ny/bookkeeper | 2026 | job posting list | current |
| 14 | Robert Half, Bookkeeper, New York NY (IT services) | https://www.roberthalf.com/us/en/job/new-york-new-york/bookkeeper/02940-0013461759-usen | 2026 | job posting | current |
| 15 | Robert Half, Remote bookkeeping jobs (list page) | https://www.roberthalf.com/us/en/jobs/all/remote-bookkeeping | 2026 | job posting list | current |
| 16 | Robert Half, Bookkeeper, Charleston SC | https://www.roberthalf.com/us/en/job/charleston-south-carolina/bookkeeper/03270-0013505084-usen | 2026 | job posting | current |
| 17 | IRS, How long should I keep records? | https://www.irs.gov/businesses/small-businesses-self-employed/how-long-should-i-keep-records | 2026 | government guidance | current |
| 18 | IRS, Publication 583, Starting a Business and Keeping Records | https://www.irs.gov/publications/p583 | 2025 | government publication | current |
| 19 | IRS, Publication 538, Accounting Periods and Methods | https://www.irs.gov/publications/p538 | 2025 | government publication | current |
| 20 | 26 CFR 1.274-5, Substantiation requirements (Cornell LII) | https://www.law.cornell.edu/cfr/text/26/1.274-5 | 2025 | regulation | canon / current |
| 21 | IRS, Publication 463, Travel, Gift, and Car Expenses | https://www.irs.gov/publications/p463 | 2025 | government publication | current |
| 22 | IRS, Tangible property final regulations | https://www.irs.gov/businesses/small-businesses-self-employed/tangible-property-final-regulations | 2025 | government guidance | current |
| 23 | IRS, Understanding the Working Families Tax Cuts: Business Tax Provisions (video script) | https://www.irs.gov/newsroom/understanding-the-working-families-tax-cuts-business-tax-provisions-youtube-video-text-script | 2025 | government guidance | current (post-OBBBA) |
| 24 | IRS, Instructions for Forms 1099-MISC and 1099-NEC | https://www.irs.gov/instructions/i1099mec | 2026 | form instructions | current (post-OBBBA) |
| 25 | IRS, Backup withholding | https://www.irs.gov/businesses/small-businesses-self-employed/backup-withholding | 2025 | government guidance | current |
| 26 | IRS, FAQs on Form 1099-K threshold under OBBB | https://www.irs.gov/newsroom/irs-issues-faqs-on-form-1099-k-threshold-under-the-one-big-beautiful-bill-dollar-limit-reverts-to-20000 | 2025 | press release / FAQ | current (post-OBBBA) |
| 27 | IRS, Independent contractor (self-employed) or employee? | https://www.irs.gov/businesses/small-businesses-self-employed/independent-contractor-self-employed-or-employee | 2025 | government guidance | current |
| 28 | HMRC, Record keeping for VAT (VAT Notice 700/21) | https://www.gov.uk/guidance/record-keeping-for-vat-notice-70021 | 2025 | government guidance | current |
| 29 | GOV.UK, Running a limited company: company and accounting records | https://www.gov.uk/running-a-limited-company/company-and-accounting-records | 2025 | government guidance | current |
| 30 | GOV.UK, Late commercial payments: charging interest | https://www.gov.uk/late-commercial-payments-interest-debt-recovery/charging-interest-commercial-debt | 2025 | government guidance | current |
| 31 | HMRC, Find out if and when you need to use Making Tax Digital for Income Tax | https://www.gov.uk/guidance/find-out-if-and-when-you-need-to-use-making-tax-digital-for-income-tax | 2026 | government guidance | current |
| 32 | IFRS Foundation, IFRS 15 Revenue from Contracts with Customers | https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/ | 2014 | accounting standard | canon |
| 33 | SEC, Staff Accounting Bulletin No. 99, Materiality | https://www.sec.gov/interps/account/sab99.htm | 1999 | regulatory interpretation | canon |
| 34 | IRS, Recordkeeping | https://www.irs.gov/businesses/small-businesses-self-employed/recordkeeping | 2025 | government guidance | current |
| 35 | OpenStax, Principles of Accounting Vol. 1, 8.6 Bank Reconciliation | https://openstax.org/books/principles-financial-accounting/pages/8-6-define-the-purpose-of-a-bank-reconciliation-and-prepare-a-bank-reconciliation-and-its-associated-journal-entries | 2019 | textbook | canon |
| 36 | OpenStax, Principles of Accounting Vol. 1, 3.6 Prepare a Trial Balance | https://openstax.org/books/principles-financial-accounting/pages/3-6-prepare-a-trial-balance | 2019 | textbook | canon |
| 37 | OpenStax, Principles of Accounting Vol. 1, 4.2 Adjusting Entries | https://openstax.org/books/principles-financial-accounting/pages/4-2-discuss-the-adjustment-process-and-illustrate-common-types-of-adjusting-entries | 2019 | textbook | canon |
| 38 | OpenStax, Principles of Accounting Vol. 1, 9.2 Uncollectible Accounts | https://openstax.org/books/principles-financial-accounting/pages/9-2-account-for-uncollectible-accounts-using-the-balance-sheet-and-income-statement-approaches | 2019 | textbook | canon |
| 39 | OpenStax, Principles of Accounting Vol. 1, 8.3 Internal Controls | https://openstax.org/books/principles-financial-accounting/pages/8-3-describe-internal-controls-within-an-organization | 2019 | textbook | canon |
| 40 | OpenStax, Principles of Accounting Vol. 1, 8.4 Petty Cash | https://openstax.org/books/principles-financial-accounting/pages/8-4-define-the-purpose-and-use-of-a-petty-cash-fund-and-prepare-petty-cash-journal-entries | 2019 | textbook | canon |
| 41 | COSO, Internal Control - Integrated Framework, Executive Summary (mirror copy hosted by the City of Columbia, MO; not a coso.org location) | https://www.como.gov/archive/2021/12/COSO-2013.pdf | 2013 | framework | canon |
| 42 | ACFE, Report to the Nations 2020 | https://acfepublic.s3-us-west-2.amazonaws.com/2020-Report-to-the-Nations.pdf | 2020 | industry study | canon |
| 43 | ACFE, Top 4 Internal Controls That Reduce Fraud Losses | https://www.acfe.com/acfe-insights-blog/blog-detail?s=top-internal-controls-that-reduce-fraud-losses-2020 | 2020 | industry study summary | canon |
| 44 | Steven M. Bragg, The Fast Close, Part 6 (AccountingTools podcast #21) | https://www.accountingtools.com/podcast-blog/21 | 2019 | practitioner podcast/blog | canon |
| 45 | Steven M. Bragg, Closing entries / closing procedure | https://www.accountingtools.com/articles/closing-entries-closing-procedure | 2026 | practitioner reference | canon concept, page updated |
| 46 | Steven M. Bragg, Three-way matching | https://www.accountingtools.com/articles/what-is-three-way-matching.html | 2026 | practitioner reference | canon concept, page updated |
| 47 | Late Payment of Commercial Debts (Interest) Act 1998, s.5A | https://www.legislation.gov.uk/ukpga/1998/20/section/5A | 1998 | statute | canon |
| 48 | GOV.UK, Invoices: what they must include | https://www.gov.uk/invoicing-and-taking-payment-from-customers/invoices-what-they-must-include | 2024 | government guidance | current |
| 49 | Wikipedia, Summa de arithmetica (Pacioli) | https://en.wikipedia.org/wiki/Summa_de_arithmetica | 1494 | encyclopedia (historical work) | canon |
| 50 | Sholto Macpherson, The experiment that suggests AI accountants won't replace you (yet) | https://publicaccountant.com.au/features/ai-accounting-future-accuracy-challenge/ | 2025 | trade press on benchmark | LLM era |
| 51 | GIGAZINE, Results of the AccountingBench benchmark | https://gigazine.net/gsc_news/en/20250724-accountingbench/ | 2025 | tech press on benchmark | LLM era |
| 52 | Benchek et al. (Mercor, Ramp), APEX-Accounting | https://arxiv.org/html/2607.27189v1 | 2026 | academic preprint | LLM era |
| 53 | Chris Gaetano, Digits says its AI agents can automate 95% of bookkeeping (Accounting Today) | https://www.accountingtoday.com/news/digits-says-its-new-ai-agents-can-automate-95-of-bookkeeping-tasks | 2025 | trade press / vendor claim | LLM era |
| 54 | Xero, First look at automatic bank reconciliation (JAX beta) | https://blog.xero.com/product-updates/automatic-bank-reconciliation-jax-beta/ | 2025 | vendor blog | LLM era |
| 55 | Xero, JAX financial superagent press release | https://www.xero.com/us/media-releases/xeros-ai-financial-superagent-jax-launches-powerful-new-features/ | 2025 | vendor press release | LLM era |
| 56 | Intuit, Virtual team of AI agents press release | https://investors.intuit.com/news-events/press-releases/detail/1258/intuit-introduces-ground-breaking-virtual-team-of-ai-agents-to-fuel-growth-for-businesses | 2025 | vendor press release | LLM era |
| 57 | Intuit QuickBooks, Learn about Accounting AI features | https://quickbooks.intuit.com/learn-support/en-us/help-article/bank-transactions/accounting-agent-features/L6pl9rv94_US_en_US | 2025 | vendor documentation | LLM era |
| 58 | Intuit QuickBooks, Agentic AI 2025 product update | https://quickbooks.intuit.com/r/product-update/innovation-agentic-ai-2025/ | 2025 | vendor product page | LLM era |
| 59 | Dong et al., Transaction Categorization with Relational Deep Learning in QuickBooks | https://arxiv.org/abs/2506.09234 | 2025 | conference paper (preprint) | LLM era |
| 60 | PYMNTS (AppZen data), AI-generated fake receipts now 71% of expense fraud | https://www.pymnts.com/news/artificial-intelligence/2026/ai-generated-fake-receipts-now-make-up-71percent-of-expense-fraud/ | 2026 | trade press / industry data | LLM era |
| 61 | FBI IC3, Business Email Compromise: The $55 Billion Scam | https://www.ic3.gov/PSA/2024/PSA240911 | 2024 | government advisory | current |
| 62 | Wikipedia, Bench Accounting | https://en.wikipedia.org/wiki/Bench_Accounting | 2025 | encyclopedia | current |
| 63 | Kelly D. Mullins, Accounting ethics in the age of AI (Journal of Accountancy) | https://www.journalofaccountancy.com/issues/2026/aug/accounting-ethics-in-the-age-of-ai/ | 2026 | professional journal | LLM era |
| 64 | Isaac Heller, The AI revolution in accounting is real. So is the new risk (Accounting Today) | https://www.accountingtoday.com/opinion/the-ai-revolution-in-accounting-is-real-so-is-the-new-risk | 2026 | opinion essay | LLM era |
| 65 | Megan Cerullo, Should you use AI to file your taxes? (CBS News) | https://www.cbsnews.com/news/can-you-use-ai-for-taxes-chatgpt-claude-irs/ | 2026 | news | LLM era |
| 66 | Randall Joens CPA, Monthly Close Checklist for Small Business (WhippleWood CPAs) | https://whipplewood.com/insights/monthly-close-checklist-for-small-business/ | 2026 | practitioner guide | current |
| 67 | HMRC, Making Tax Digital for Income Tax: step by step | https://www.gov.uk/government/collections/making-tax-digital-for-income-tax-for-sole-traders-and-landlords-step-by-step | 2026 | government guidance | current |
| 68 | Intuit, 2025 QuickBooks accountant survey press release | https://investors.intuit.com/news-events/press-releases/detail/1263/accountants-embrace-ai-and-strategic-advisory-services-to-fuel-growth-yet-continue-to-face-tech-and-talent-barriers-according-to-2025-intuit-quickbooks-survey | 2025 | vendor-commissioned survey | LLM era |
| 69 | BLS, Occupational Outlook Handbook: Bookkeeping, Accounting, and Auditing Clerks | https://www.bls.gov/ooh/office-and-administrative-support/bookkeeping-accounting-and-auditing-clerks.htm | 2026 | government statistics | current |
| 70 | Stanford Digital Economy Lab, AI employment gap for young workers | https://digitaleconomy.stanford.edu/news/canariesaug26/ | 2026 | academic research update | LLM era |
| 71 | Penrose team, AccountingBench discussion (Hacker News) | https://news.ycombinator.com/item?id=44637352 | 2025 | practitioner discussion | LLM era |
| 72 | Islam et al., FinanceBench | https://arxiv.org/abs/2311.11944 | 2023 | academic paper | LLM era |
| 73 | ACFE, Key Findings: Occupational Fraud 2026 | https://www.acfe.com/acfe-insights-blog/blog-detail?s=key-findings-report-to-the-nations-2026 | 2026 | industry research | current |
| 74 | GrowthForce, Divide and conquer business fraud with separation of duties | https://www.growthforce.com/blog/divide-and-conquer-business-fraud-with-separation-of-duties | n.d. | practitioner blog | current |
| 75 | IRS, Employment taxes and the Trust Fund Recovery Penalty | https://www.irs.gov/businesses/small-businesses-self-employed/employment-taxes-and-the-trust-fund-recovery-penalty-tfrp | n.d. | government guidance | current |
| 76 | Rachel Blakely-Gray, 1099 threshold increases to $2,000 (Patriot Software) | https://www.patriotsoftware.com/blog/accounting/1099-reporting-threshold/ | 2026 | vendor/practitioner article | current (post-OBBBA) |
| 77 | Steven Bragg, Accounting for sales taxes (AccountingTools) | https://www.accountingtools.com/articles/accounting-for-sales-taxes | 2026 | professional reference | current |
| 78 | AccountingCoach, Recording a loan payment with interest and principal | https://www.accountingcoach.com/blog/interest-principal-loan-payments | n.d. | professional reference | timeless |
| 79 | Intuit QuickBooks, Fix duplicate transactions in QBO bank feeds | https://quickbooks.intuit.com/learn-support/en-us/help-article/duplicate-transactions/fix-duplicate-transactions-quickbooks-online-bank-feeds/L1fjxl88f_US_en_US | 2026 | vendor documentation | current |
| 80 | Intuit QuickBooks, Lock your books in QBO | https://quickbooks.intuit.com/learn-support/en-us/help-article/close-books/close-books-quickbooks-online/L59LelyPM_US_en_US | 2026 | vendor documentation | current |
| 81 | GrowthForce, Risks of commingling funds: piercing the corporate veil | https://www.growthforce.com/blog/piercing-the-corporate-veil | n.d. | practitioner blog | current |
| 82 | Intuit TurboTax blog, Mixing business and personal Venmo | https://blog.turbotax.intuit.com/self-employed/confession-ive-been-mixing-my-business-and-personal-venmo-140479/ | n.d. | vendor blog | current |
| 83 | The Tax Adviser (AICPA & CIMA), The de minimis and routine maintenance safe harbors | https://www.thetaxadviser.com/issues/2024/may/the-de-minimis-and-routine-maintenance-safe-harbors/ | 2024 | professional journal | current |
| 84 | IRS, Common questions about recordkeeping for small businesses | https://www.irs.gov/newsroom/common-questions-about-recordkeeping-for-small-businesses | n.d. | government guidance | current |
| 85 | Charles Rollet (TechCrunch via Yahoo Finance), Bench shuts down | https://finance.yahoo.com/news/bench-shuts-down-leaving-thousands-215200329.html | 2024 | news | current |
| 86 | Sales Tax Institute, Wayfair case and economic nexus | https://www.salestaxinstitute.com/sales_tax_faqs/wayfair-economic-nexus | n.d. | professional reference | post-Wayfair |
| 87 | Intuit QuickBooks, Manually upload transactions into QBO | https://quickbooks.intuit.com/learn-support/en-us/help-article/import-transactions/manually-upload-transactions-quickbooks-online/L0rE9OXBz_US_en_US | 2026 | vendor documentation | current |
| 88 | Intuit QuickBooks, Deposit payments into Undeposited Funds | https://quickbooks.intuit.com/learn-support/en-us/help-article/payroll-setup/deposit-payments-undeposited-funds-account-online/L1td0m8Z2_US_en_US | 2026 | vendor documentation | current |
| 89 | Intuit QuickBooks, Undo or remove transactions from reconciliations | https://quickbooks.intuit.com/learn-support/en-us/help-article/accounting-bookkeeping/undo-remove-transactions-reconciliations-online/L6ERlEXxn_US_en_US | 2026 | vendor documentation | current |
| 90 | Book Tech LLC, Bank reconciliation report in QBO | https://www.booktechusa.com/post/bank-reconciliation-report-quickbooks-online | n.d. | practitioner guide | current |
| 91 | BB Books Inc, Xero the Hero: The Bank Reconciliation Summary | https://bbbooksinc.com/blog/the-bank-reconciliation-summary/ | n.d. | practitioner guide | current |
| 92 | Saint & Co (Michelle Ruddick), Is Xero showing the correct bank balance | https://www.saint.co.uk/is-xero-showing-correct-bank-balance-why-this-should-matter-to-you/ | 2023 | practitioner guide | current |
| 93 | CheckFree, Intuit, Microsoft, Open Financial Exchange Specification 1.0 | https://xml.coverpages.org/OFEXFIN1.html | 1997 | technical specification | canon (historical-foundational) |
| 94 | Stripe, Payout reconciliation report | https://docs.stripe.com/reports/report-types/payout-reconciliation | 2026 | vendor documentation | current |
| 95 | Stripe, Balance summary report | https://docs.stripe.com/reports/balance | 2026 | vendor documentation | current |
| 96 | PayPal Developer, Activity Download report | https://developer.paypal.com/docs/reports/online-reports/activity-download/ | 2026 | vendor documentation | current |
| 97 | Intuit QuickBooks, Why aging reports have both Current and 1-30 | https://quickbooks.intuit.com/learn-support/en-us/help-article/accounts-payable-reports/aging-reports-current-1-30/L43pItdAj_US_en_US | 2026 | vendor documentation | current |
| 98 | Intuit QuickBooks, Run an accounts receivable aging report | https://quickbooks.intuit.com/learn-support/en-us/help-article/accounts-receivable-reports/run-accounts-receivable-aging-report/L4N7PC2hg_US_en_US | 2026 | vendor documentation | current |
| 99 | Intuit QuickBooks, Run reports in QBO (accounting method) | https://quickbooks.intuit.com/learn-support/en-us/help-article/report-management/run-reports-quickbooks-online/L7aILHhbl_US_en_US | 2026 | vendor documentation | current |
| 100 | Intuit QuickBooks, Set up bank rules | https://quickbooks.intuit.com/learn-support/en-us/help-article/banking/set-bank-rules-categorize-online-banking-online/L0mjJl0nD_US_en_US | 2026 | vendor documentation | current |
| 101 | Intuit QuickBooks, Enter and manage opening balances | https://quickbooks.intuit.com/learn-support/en-us/help-article/bank-deposits/enter-opening-balance-account-quickbooks-online/L7NcxTbuu_US_en_US | 2026 | vendor documentation | current |
| 102 | Intuit QuickBooks, Download the most recent bank and card transactions | https://quickbooks.intuit.com/learn-support/en-us/help-article/multi-factor-authentication/download-recent-bank-credit-card-transactions/L86TTVI3Y_US_en_US | 2026 | vendor documentation | current |
| 103 | David Harding, Xero invoice status Authorised: what approved really means | https://invoicedataextraction.com/blog/xero-invoice-status-authorised | 2026 | practitioner guide | current |
| 104 | AutoGPT platform, "What a skill package can use" (capabilities.md, `origin/dev` febfb867) | internal: skill-forge/capabilities.md | 2026 | internal code-verified reference | current |
| 105 | Skill-forge job research file: duty tallies and pay figures over the 14 postings [1]-[16], with quoted duty lines per posting | internal: skill-forge/bookkeeping/research-jobs.json | 2026 | internal research notes | current |

Sources in the research files not cited above but consulted: [34] (recordkeeping system choice,
supports "adapt to the user's chart"), [49] (historical framing only), [55][56][58][68][70]
(market context for AI adoption and role change).
