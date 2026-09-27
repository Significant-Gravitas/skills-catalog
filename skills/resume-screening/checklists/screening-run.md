# Screening run (mirror in TodoWrite)

1. `find_rubric.py <role> --emit-criteria`: exit 0 and checksum ok (missing only for Sofia or a `--file` rubric; exit 3 or 4: stop).
2. Law-watch lines for each `law_watch` region (or "jurisdictions not recorded").
3. Inputs saved into `/home/user/screen/<role>/<date>/in/` (uploads, Drive, pasted text as .txt).
4. ATS export: `redact_export.py` first; one line naming dropped columns and one naming moved proxy columns.
5. `extract_resumes.py` (with `--dnc` for Sofia): needs-a-look ids, held count, FACT lines noted.
6. `redact.py`: id map written to the durable batch folder; never read back into the conversation. "No name line" ids stay on needs-a-look until the owner fills their `name_hint` in the id map and `redact.py` is re-run.
7. One pass per record with `templates/screen-subtask-prompt.md` (one Task sub-agent per record, at most 3 at once; else one run_sub_session per record; else same-context passes, and the owner is told they were not isolated). JSON to `records/<id>.json`.
8. `verify_quotes.py records red`.
9. `merge_matrices.py`: no PROBLEM or UNVERIFIED lines left unexplained.
10. `batch_counts.py`: numbers used verbatim.
11. Files saved to the durable batch folder and delivered by link.
12. Summary from `templates/batch-summary.md`; no ranking; decisions left to the owner.
13. Sofia: ask once about tracker write-back; run `tracker_mark_screened.py` only on a yes.
14. Self-check from SKILL.md.
