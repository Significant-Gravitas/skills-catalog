# Pay terms: where numbers may come from

Citations `[n]` are in `references/sources.md`. Law as read on 2026-09-27;
confirm the hiring jurisdiction with the people lead or counsel.

## Allowed sources for any pay figure

- A named, authorised approver's written approval (email, approval record,
  or the hiring plan's approved band with the approver's name), and
- the company's offer template for currency, pay period and fixed wording.

Every figure in `terms.json` carries its source, approver and date.
`check_terms.py` rejects a filled term without them.

## Never a source

| Not a source | Why |
|---|---|
| The candidate's current or past pay, even if volunteered or already in the notes | Salary-history bans: California employers may not seek salary history or rely on it in deciding whether to offer or what to pay [56]. Many other states and cities have similar bans [75]. Harper's rule is stricter than any single law: never ask, record, derive, or match |
| "Match her current salary plus 10%" and similar instructions | The same rule applies. Harper declines and asks the approver for the figure from the approved band |
| Market data, benchmarks, salary sites, "typical for the level" | Harper does not estimate pay or bands. Only the approver sets pay |
| Another candidate's offer, or an earlier draft | Terms are per offer and per approval |
| The candidate's stated expectations | They can inform the approver, but they are not a term. The approver sets the figure |

## Pay transparency

Some jurisdictions require a pay range in postings, and some require
disclosure on request. For example, California employers with 15 or more
employees must include a good-faith pay scale in postings [56], and Colorado
requires a pay range and a benefits description [57]. At the offer stage,
Harper only flags: "An offer outside the posted range may need a word from
the people lead." Harper never picks a figure.

## Sales roles

When the role has variable pay (OTE, commission, quota), the letter and email
state it only as the approver's text, word for word, from the approved plan
document. Harper never computes OTE or explains the commission mechanics.
Practitioner judgement (unsourced), consistent with the dossier's J9.

## Changes after the draft

Any change to compensation or conditions needs fresh written approval,
recorded as a new `approved_on` entry. That includes a counter-offer the
candidate raises or "the manager said we can go a bit higher". Harper never
negotiates, and never tells the candidate what is possible.
