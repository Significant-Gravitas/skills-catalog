# Metric definitions

What each number in the report means, how `scripts/funnel.py` computes it,
and the trap behind it. Dated 2026-09-27; bracketed numbers are sources in
references/sources.md. Unsourced lines say "practitioner judgement".

## Contents
1. Funnel stages and the two views
2. Conversion and "biggest loss"
3. The two clocks, plus time to slate
4. Days in stage, stalls, reqs with no movement
5. Source mix and source of hire
6. Offer acceptance and decline reasons
7. Quality of hire (early attrition) and hiring-manager satisfaction
8. Outreach reply types and follow-ups due
9. Labels, small samples, and what is never computed

## 1. Funnel stages

Ladder: **entered** (sourced into process, or applied) -> **screened** ->
**in loop** -> **offer** -> **hired**. Closed outcomes: rejected (we),
withdrew (they), declined offer (they). The owner's stage names stay in
their words; `pipeline_io.DEFAULT_STAGES` plus `--stage-map` map them. An
unmapped stage is listed under hygiene, never guessed.

- **Prospects are not applicants** [86]. Rows with `is_prospect` (or stage
  "prospect") are counted separately and excluded from the funnel.
- **Cohort view** (when rows carry entry dates such as `applied_on`): people
  who entered in the window, and how far each got. This is the default when
  an ATS export is normalised.
- **All-rows view** (Sofia's tracker, which has no entry dates): every row
  in the tracker, compared with the previous snapshot. The report says which
  view it used in its first banner.
- A candidate "reached" a stage if their current or furthest stage is at or
  beyond it. An offer date means the offer stage was reached.

## 2. Conversion and biggest loss

- Conversion = reached next stage / reached this stage.
- **Open cohorts understate conversion**: people still active may move on.
  Conversions are labelled INFERENCE when the cohort is open or when closed
  rows have no furthest stage (they count at "entered" only - a lower bound).
- Ashby's passthrough report is a closed cohort by default and treats
  skipped stages as passed [94]; never compare it directly with an
  open-cohort number.
- **Biggest loss** = the stage where the most people closed (rejected,
  withdrew, declined), with the top two reasons in plain words. Reasons come
  from the reason column, or from `notes` on closed rows in Sofia's tracker.
- Keep "we rejected them" apart from "they withdrew" [87] - they need
  different fixes.

## 3. Clocks

| Metric | From -> to | Trap |
|---|---|---|
| Time to hire | entry (applied or sourced) -> accepted | Snapshot-derived entry dates are INFERENCE, accurate to the snapshot interval |
| Time to fill | opening open date -> accepted | Greenhouse's time-to-fill "Days to hire" starts at the opening's open date, not the application [83]; evergreen openings make it unreliable [85] |
| Time to slate | opening open date -> slate ready (roles.csv `slate_ready_on`) | UNKNOWN unless both dates exist |

Zero-day and negative durations are data-entry artefacts: listed under
hygiene, never averaged. [84]'s zero-day case is a fill of 0 days (hired the
day the opening was marked open); an applied-and-hired-the-same-day time to
hire is practitioner judgement (unsourced). Medians, not means (practitioner judgement:
one stuck req skews a mean at these sample sizes).

## 4. Days in stage and stalls

- Source order: the tracker's `days_in_stage`; else today minus
  `stage_entered_on`; else the snapshots (INFERENCE); else UNKNOWN.
- Stalled = over the owner's `stalled_bar` in preferences.md (default 5
  business days - default, confirm with the owner). The report names the
  oldest five stuck with owner and who they wait on.
- A role where every active person is over the bar is flagged "no movement"
  (the req is aging).
- **Req age** = today minus `opened_on` (roles.csv) for each open req, in
  days [FACT]; UNKNOWN when there is no `opened_on`. Read it next to "no
  movement": an old req with no movement is the one to raise.
- A stall already reported becomes one rollup line with the date first
  reported (snapshot_and_chart.py diff).

## 5. Source mix and source of hire

- Source mix = the source column across the cohort (sourced, inbound,
  referral, or the ATS's own source names).
- Source of hire = the source of each hire in the window.
- Referrals can be up to 48% of hires, and their performance edge fades if
  the referrer leaves [36]; an all-referral slate is a homogeneity risk
  worth one line [34].
- A Greenhouse merge drops source and referral credit [91]: duplicates
  resolved by merging can shift source of hire. Until the owner merges,
  funnel.py counts a duplicate name + role once (furthest stage, then the
  latest stage date) and lists it under hygiene.

## 6. Offer acceptance

- Accepted / (accepted + declined) for offers resolved in the window (the
  offer date stands in when there is no resolution date). Offers still open
  are reported separately; unresolved offers are one of the data traps
  Greenhouse's data-accuracy guide describes [84].
- A row rejected by the candidate after an offer went out counts as a
  declined offer.
- Monthly (first Friday): acceptance over the previous calendar month,
  from the snapshots - offers accepted or declined in that month, one per
  name + role, latest state wins - labelled with the month and n; "-" when
  n=0.
- Offers past their answer-by date come from
  `~/workspace/hiring/offers/*/close-plan.csv` (job-offer-and-close-plan).

## 7. Quality

- **Early attrition** = hires who left within the window (default 90 days -
  default, confirm with the owner) of their start date, among hires whose
  start date is at least that long ago. Needs a hires file; exit notes
  grouped, only as the owner wrote them.
- **Hiring-manager satisfaction** appears in some postings as a recruiter
  KPI [5]. Reported only from survey results the owner supplies, as percent
  of scale maximum with n.
- **Cost per hire**: see references/cost-per-hire.md.

## 8. Outreach

- Reply types are reported separately. An InMail "response" includes "Not
  interested" [96], so never call all responses positive.
- The rule is passive-candidate-outreach's (its `followups_due.py`), so
  both skills give the same list on the same log:
  - `outreach_cadence` = days after the first note (default 2, 5, 8);
  - `outreach_day_kind` = business (default: weekdays only) or calendar
    (every day, a weekend due date rolls to Monday); no holiday list;
  - `touch_limit` = follow-ups after the first note (default 3, so the
    sequence is complete after touch 4). All defaults - confirm with the
    owner.
- A follow-up due today or earlier is listed with its touch number, due
  date and working days late. Drafts come from passive-candidate-outreach
  (`read_skill`), never from this skill.
- Same as `followups_due.py`: a not-now reply is listed once when its
  check_back_date has arrived ("one check-back note, then stop"); a touch
  already in the log as drafted is marked "draft already in the log -
  confirm it was sent, do not draft again"; a touch 1 that is only drafted
  is listed as not confirmed sent. When `touch_limit` exceeds the cadence
  days, the follow-up with no cadence day is listed for the owner and
  hygiene shows "outreach cadence mismatch".
- Sequence complete with no reply: listed under hygiene; the action is to
  stop.

## 9. Labels, samples, and what is never computed

- FACT = counted from a named file. INFERENCE = derived, with the maths
  shown. UNKNOWN = missing; never filled.
- Below `min_sample` (default 30 people - default, confirm with the owner)
  the report carries a SMALL SAMPLE banner: read rates as directional.
- **Never computed:** any rate by gender, race, ethnicity, age, disability,
  veteran status or any other protected group, and no inferred
  demographics. Adverse-impact analysis (the four-fifths rule is a rule of
  thumb, not a safe harbour, and small samples may be inconclusive
  [33][41]) is run by HR or counsel on aggregated self-ID data held apart
  from recruiters [89][99].
