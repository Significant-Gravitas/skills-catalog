# GitHub evidence for engineering roles

GitHub is the one integration with a token inside the sandbox: when it is
connected, `GH_TOKEN`/`GITHUB_TOKEN` are injected and `gh` works through
`bash_exec` [114]. This catalog entry lists GitHub as the skill's required
provider for that reason.

## Contents
1. Connect
2. Commands
3. What counts as evidence
4. Rules
5. Rate limits

## 1. Connect

```
bash_exec: gh auth status
```
If not authenticated: `run_capability(id="tool:connect_integration", input={"provider": "github"})`.
That shows a card to the owner; keep sourcing from other channels meanwhile
and come back to GitHub once connected. Never ask for a token in chat.

## 2. Commands (run with bash_exec; output is JSON, trimmed with --jq)

Find people by topic (users search):
```
gh api -X GET search/users -f q='location:Berlin language:Go followers:>10' -f per_page=20 --jq '.items[] | .login'
```
Find repos on a must-have topic, then their owners:
```
gh api -X GET search/repositories -f q='stripe webhook retry in:name,description,readme' -f sort=stars -f per_page=20 --jq '.items[] | [.full_name, .html_url, .stargazers_count, .pushed_at] | @tsv'
```
A person's public profile (published fields only):
```
gh api users/<login> --jq '[.login, .name, .company, .location, .html_url] | @tsv'
```
Their recent non-fork repos:
```
gh api 'users/<login>/repos?sort=pushed&per_page=30' --jq '.[] | select(.fork|not) | [.name, .html_url, .description, .pushed_at] | @tsv'
```
Merged PRs into other people's projects (collaboration evidence):
```
gh api -X GET search/issues -f q='author:<login> is:pr is:merged -user:<login>' -f per_page=20 --jq '.items[] | [.title, .html_url, .closed_at] | @tsv'
```
Commit search for a keyword:
```
gh api -X GET search/commits -f q='author:<login> migration' -f per_page=10 --jq '.items[] | [.commit.message, .html_url] | @tsv'
```

Every URL printed by `gh api` for that login counts as fetched: record it in
`links.csv` with the person's name as `<url>,<name>,ok,yes` (the page is the
person's own profile or their authored item), and put the login in the card's
`github` field. A repo under someone else's login is not this person's
evidence unless the page names them.

## 3. What counts as evidence

| Counts | Does not count |
|---|---|
| A maintained, non-fork repo on the must-have topic | Forks, tutorial clones, course homework |
| Merged PRs into third-party projects on the topic | Stars given, followers |
| Release credits, changelogs naming them | Repo count, contribution graph colour |
| Design docs, RFCs, ADRs in public repos | Language percentages |

## 4. Rules

- Record `name`, `company`, `location` exactly as the profile publishes them,
  "as stated". Empty means UNKNOWN.
- **Never output emails**, including commit emails. They are not a published
  contact route; outreach goes through `passive-candidate-outreach`.
- Never read a personal README or pinned repos for personal-life details; take
  only professional work.
- Nothing from avatars (no reading anything off a photo).
- An org or company field is not proof of current employment; say "company as
  stated on GitHub".

## 5. Rate limits

GitHub search endpoints have a lower rate limit than other endpoints. Read the
live numbers instead of assuming: `gh api rate_limit --jq '.resources.search'`.
If `remaining` is low, pause the GitHub branch and continue with web sources.

Sources: [sources.md](sources.md).
