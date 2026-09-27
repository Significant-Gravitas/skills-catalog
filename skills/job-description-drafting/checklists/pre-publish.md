# Pre-publish checklist (the owner publishes; you hand this over with the draft)

**Bar**
- [ ] Scorecard status `approved`. If not: routed to role-intake-and-scorecard for the HM's approval; only if the owner insisted on a posting now, it opens with "Draft pending calibration" and is not published until the scorecard is approved
- [ ] `mirror_check.py` exit 0 against the current scorecard version (nice-to-haves only from the scorecard's `## Nice-to-haves`; if it says "none agreed", the posting has no nice-to-have section, and any posting nice-to-have shows as ADDED, exit 1)
- [ ] No years/degree floor unless the scorecard records "HM defended"; the defence note itself stays out of the posting

**Language**
- [ ] `jd_lint.py`: every FLAG swapped or defended in one line
- [ ] CHECK hits read in context
- [ ] Every line also read against `references/protected-traits-and-proxies.md`; proxies the lint missed are reported with line numbers (the lint is a backstop)
- [ ] No laundry list, no insider jargon
- [ ] Location written as work terms; physical demands "with or without reasonable accommodation"

**Facts**
- [ ] Title, level, location, start date exactly as stated
- [ ] Pay range and benefits as stated, or `[OWNER TO CONFIRM — may be required for <place>]`
- [ ] How and by when to apply (no "open until filled" where that is flagged)
- [ ] Accommodation line with a real contact or `[OWNER TO CONFIRM]`
- [ ] AI-use line only if the owner has a policy
- [ ] Anti-scam line if the owner wants it
- [ ] Equal-opportunity close

**Files**
- [ ] `posting-v<N>.md` saved (no overwrite), `.html` and `.txt` rendered; `render_posting.py` gave no unresolved-field warning (otherwise the copies are stamped drafts)
- [ ] Copies delivered via `write_workspace_file`, linked
- [ ] People-lead line for every jurisdiction flag
- [ ] "Not posted anywhere." Publishing is the owner's explicit yes, per action
