# Building the target map

## Contents
1. Target companies
2. Link checks
3. Boundaries
4. Title variants, including dark matter
5. Evidence sources by function

## 1. Target companies

Aim for 10 to 20 (default — confirm with the owner) companies where this work
really happens: same problem, similar stage and size, similar product. Build
them from search, never from memory alone.

- `web_search` quick queries (never `deep=true` unless the owner asks for a
  market study; it costs about 100x [114]). Three or more variants:
  - `"<problem>" startup engineering blog <region>`
  - `companies using <technology> at scale <domain>`
  - `<product category> <stage, e.g. "Series B"> <region>`
- Keep each company's reason (`why`) in one line tied to the scorecard: "runs
  its own billing stack" beats "good engineering culture".

## 2. Link checks

For each company, `web_fetch(url)` its site (100 KB cap, 15 s timeout [114]).
Record `link_status` in `target-companies.csv`:

- `ok`: page loads and names the company.
- `blocked`: 403, bot wall or login wall. Keep, but "check manually".
- `dead`: DNS failure, 404, parked domain. Drop the row.

A company with no working link is dropped; `scorecard_check.py --companies`
refuses rows without `ok` or `blocked`.

## 3. Boundaries

Ask the owner once:
- Are direct competitors fair game?
- Which companies are off limits: customers, partners, investors' portfolio,
  anyone under a non-solicit clause?
Keep off-limits companies on the list with the boundary noted so sourcing skips
them deliberately rather than rediscovering them.

## 4. Title variants, including dark matter

Five to ten (default) current and adjacent titles. Keyword and title searches
systematically miss qualified people whose profiles do not use the expected
terms; Cathey's examples include tens of thousands of Java engineers who never
mention "Java" [37]. So include at least two "dark matter" variants: titles
for people doing the work under another name (for billing: "Revenue
Engineer", "Monetisation Engineer"; for recruiting ops: "People Systems").
Never present one search as the whole market.

## 5. Evidence sources by function

| Function | Where people leave public proof |
|---|---|
| Engineering | Public code, maintained packages, release credits, conference talks, engineering blogs |
| Design | Portfolios, case studies, talks |
| Marketing, research | Articles, talks, published research |
| Support, solutions | Forum answers, help-center writing |
| Sales, finance | Panels, podcasts, published decks |

Only professional work goes on the map. Nothing from private life, and no
search designed to surface health, family or genetic information [47].

Sources: [sources.md](sources.md).
