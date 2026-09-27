# One screen, two kits: Harper and Sofia

This skill ships in both kits. Every rule of both personas holds, whichever
expert runs it.

## Result states

| Harper (record) | Sofia (label) | Meaning |
| --- | --- | --- |
| `EVIDENCE FOUND` | FACT (quoted, with location) | The resume states it; the quote is verified |
| `EVIDENCE MISSING` | UNKNOWN (not stated) | The document does not state it; not a negative fact |
| `CONFIRM IN INTERVIEW` | UNKNOWN (confirm in interview) | A claim lacks scope, ownership or result; or a quote failed verification |

The screen writes no INFERENCE lines about a candidate. Sofia's INFERENCE label
is for her own reads elsewhere (for example a funnel pattern), with the
reasoning shown; a screening record has none. `matrix.csv` carries both
columns (`result`, `sofia_label`).

## Where the approved bar lives

| Kit | File | Approval stamp |
| --- | --- | --- |
| Harper | `~/workspace/hiring/<role-slug>/rubric-v<N>.md` | header `status: approved`, `approved_by`, and `rubric-v<N>.md.sha256` from hiring-rubric-design |
| Sofia | `~/workspace/hiring/roles/<role-slug>/scorecard.md` | header `status: approved`, `approved_by` from role-intake-and-scorecard; must-haves M1..., nice-to-haves N1... |

`find_rubric.py` reads both. If neither exists or neither is approved, stop:
Harper runs role-intake-and-job-description then hiring-rubric-design; Sofia
runs role-intake-and-scorecard. Never screen against a job description alone.

## Where results go

| Kit | Batch folder |
| --- | --- |
| Harper | `~/workspace/hiring/<role-slug>/screens/<YYYY-MM-DD>/` |
| Sofia | `~/workspace/hiring/screens/<role-slug>/<YYYY-MM-DD>/` |

Scratch copies (raw uploads, extracted text) live under
`/home/user/screen/<role-slug>/<YYYY-MM-DD>/` and are not kept.

## Sofia-only rules that bind this skill

- **Tracker write-back only on a yes.** After the matrix is final, ask once;
  on the owner's yes, run `tracker_mark_screened.py`. It sets stage
  "screened" and "owner decision"; it never writes a result, quote or score
  into the tracker.
- **Do-not-contact.** Pass `~/workspace/hiring/dnc.csv` to
  `extract_resumes.py --dnc`. A match is held back: no text, no record, only a
  count in the output. The owner sees who in the manifest. Names match as
  whole words with accents, case and word order ignored: "Jose Perez" holds
  "José Pérez" and "PEREZ, Jose"; "Ann Lee" never holds "Joann Leeds".
  The tracker write-back skips a "do not contact" row the same way.
- **Delete on request, same reply.** "Remove <name>" runs
  `forget_candidate.py` immediately, without asking why. It clears the batch
  files; list any delivered copies and the tracker row for the owner. The
  name matches with or without accents; if it matches two records, ask
  which one in that same reply. If the file came from a .zip, the zip
  still holds it: say so.
- **Protected columns.** Dropped from any export, with one line saying which.
- **No candidate details in a group channel.** Results are delivered as files
  to the owner, never posted to chat.
- **Recommend, never decide.** Sofia recommends with evidence elsewhere; in
  this skill the output is the matrix. No ranking, no tie-breaks.

## Harper-only rules that bind this skill

- Three outcomes only, each with the resume text behind it.
- Drafts only; no candidate message from this skill.
- Never rank, advance, reject, or recommend a final decision.

## What both share

Sofia's sourcing skill orders *sourced prospects* by benchmark match; that is
a different skill and a different population. Inbound applicants in this
skill are never ordered, ranked or shortlisted by the screen.
