# ATS and export traps on import

Most recruiter postings name no tool, so the tracker works from a paste, an
upload or an export [1]. When the export comes from an applicant tracking
system (ATS), these traps change what the numbers and rows mean.
`[n]` numbers follow the recruiting dossier (section 8).

| System | Trap | What the import does |
| --- | --- | --- |
| Greenhouse | Prospects are not applicants; prospect records mix into candidate lists [86] | Keeps `is_prospect=yes`; stall sweeps skip prospects |
| Greenhouse | Merging candidates drops the secondary profile's source and referral credit [91] | Never merges on a guess; possible duplicates go to needs-a-look for the owner |
| Greenhouse | Harvest v1/v2 APIs were removed on 2026-08-31; anything built on them fails [88] | Ask for a UI export or a v3 connector |
| Greenhouse | Harvest v3 `GET /v3/eeoc` returns row-level self-ID keyed by application and candidate id [118], unlike the anonymised in-app EEOC report [89] | Protected and self-ID columns dropped before reading |
| Greenhouse | Scorecard visibility can let interviewers see others' feedback before filing [90] | Noted for the debrief skill; not a tracker field |
| Lever | Contacts and opportunities are separate objects; archive reasons are stored as ids [93] | One candidate row per person per role (opportunity); ask the owner to map archive-reason ids to words |
| Ashby | Passthrough report is a closed cohort by default, treats skipped stages as passed, and exports only as PDF [94] | A PDF is refused; ask for a candidate-list CSV |
| Workday | Automatic candidate merging is narrow, so name-variant duplicates survive [92] | Close-name check puts them on needs-a-look |
| LinkedIn Recruiter | CSV exports exclude member-entered contact data, are capped at 5,000 per month per seat, and Recruiter Lite cannot export CSV [97] | Contact routes are never filled from an export |

Import checklist:
1. Pull the file in: `read_workspace_file(file_id=..., save_to_path="/home/user/coord/export.csv")`.
2. `merge_tracker.py import --list candidates --incoming /home/user/coord/export.csv --dry-run`.
3. Read "Dropped", "Not imported", "needs a look" and ambiguous dates; ask the
   date order once if needed (`ask_question`, options "day/month" and "month/day").
4. Run without `--dry-run`; report added / updated / unchanged counts and the
   needs-a-look list in the same reply.

## Sources

| # | Source | URL |
| --- | --- | --- |
| 1 | Recruiter postings tally (dossier research file) | internal (research-jobs.json) |
| 86 | Greenhouse, Prospects overview | https://support.greenhouse.io/hc/en-us/articles/200670155-Prospects-overview |
| 88 | Greenhouse Harvest API deprecation | https://docs.greenhouse.io/harvest.html |
| 89 | Greenhouse, EEOC report | https://support.greenhouse.io/hc/en-us/articles/204636035-Equal-Employment-Opportunity-Commission-EEOC-report |
| 90 | Greenhouse, Scorecards FAQ | https://support.greenhouse.io/hc/en-us/articles/15756249510427-Scorecards-FAQ |
| 91 | Greenhouse, Merge candidate data | https://support.greenhouse.io/hc/en-us/articles/115004506466-How-does-the-merge-candidate-option-work-and-what-points-of-data-are-deprecated- |
| 92 | Workday, Automatic Candidate Merging | https://doc.workday.com/admin-guide/en-us/human-capital-management/recruiting/candidates/duplicate-candidate-merging/kfk1502452337000.html |
| 93 | Lever API documentation | https://hire.lever.co/developer/documentation |
| 94 | Ashby, Passthrough Report FAQ | https://docs.ashbyhq.com/passthrough-report-features-and-faq |
| 97 | LinkedIn Help, Export profiles in Recruiter | https://www.linkedin.com/help/recruiter/answer/a412149 |
| 118 | Greenhouse Harvest v3, List EEOC | https://harvestdocs.greenhouse.io/reference/get_v3-eeoc |
