---
name: "gtm-account-sourcing"
description: "Use when the user wants real accounts, not a profile: a list of businesses that fit the ICP, local businesses in an area, podcasts to pitch or prospects' podcast appearances, a qualification pass over a list, or a prospect's site read end to end. Builds the list with Exa, qualifies it with Parallel Decisions, and crawls sites with ZenRows."
triggers: ["build a target account list", "find businesses in", "local businesses", "lead list", "podcasts to pitch", "podcast appearances", "qualify this list", "score these accounts", "crawl their site", "enrich these accounts"]
version: "1"
---

# GTM account sourcing

Use this when the ICP has to turn into named accounts: a list of
businesses that fit, local businesses in an area, podcasts to pitch or to
mine for a prospect's own words, a qualification pass over a list the user
already has, or one prospect's site read end to end. Start from the ICP
memo in files (or draft one with `icp-and-segmentation` first), the
geography, and how many accounts the motion can actually work. A list
nobody can work this month is waste; size it to the team.

Three tools, one job each. Pick the cheapest one that answers the question.

## Find: Exa search, including places and podcasts

Run **Exa Search**. Exa's index now covers places (about 211M businesses
and venues, with name, category, address, opening hours, phone, website
and ratings) and podcasts (about 3.2M episodes with full transcripts,
hosts and guests). Neither has its own category or endpoint: describe what
you want in plain language in the query and Exa finds it.

- **Places.** Name the business type and the area in the query: "physical
  therapy clinics in Leeds with online booking", "independent coffee
  roasters in Portland that sell wholesale". Leave the category empty.
  Set the user location to the country code when the area alone is
  ambiguous. Ask for up to 100 results per search, and split a big
  territory into neighbourhoods or towns rather than one vague query.
- **Podcasts.** Two uses. To find shows to pitch or sponsor: "podcasts
  about running a dental practice", then read who hosts them and who they
  have had on. To find a prospect's own words: "podcast episodes where
  <name> of <company> talks about <the problem you solve>". A quote from
  their own episode is the strongest trigger there is; save it with the
  episode link and date.
- **Companies and people.** Use the company or people category for the
  firmographic and persona blocks of the ICP.

Ask for text or highlights in the contents so the place or episode
details come back. The fields arrive in the result text, not in fixed
columns, so read the first results before you shape the table, and note
any field that never appears. Exa search costs well under a cent per
query; say the count of searches before a run over a large territory.

## Qualify: Parallel Decisions

Parallel answers typed questions about one subject from fresh web
evidence, up to 100 questions per request at the price of one, so it
replaces reading each account by hand.

Run **Parallel Ask Many Decisions** once per account, with the account's
name and website as the context and the ICP's fit signals and
anti-signals as the questions:

- yes/no (noul) for each signal: "Has more than one location", "Is
  hiring for a sales role", "Sells to enterprise customers". Write the
  true and false criteria when the line is fuzzy.
- choice for tiering: strategic, growth, watch, or unknown. Always give
  an unknown option.
- score for overall fit, with the Best/Good/Bad rubric from the ICP memo
  as the levels, lowest first.

Group questions about one account into one request; never mix two
accounts in one. A yes/no answer is a probability, not a verdict: treat
0.8 and above as yes, 0.2 and below as no, and everything between as
UNKNOWN for a human look. A refused question is UNKNOWN, never a no.
Citations cover the whole request, not one answer, so quote them as the
evidence for the row. For a single question, the **Parallel Yes No
Decision**, **Parallel Choice Decision** and **Parallel Score Decision**
blocks do the same with a simpler output.

## Read the site: ZenRows crawl

When one account matters enough to read in full (pricing, careers, case
studies, docs, customer logos), crawl it rather than fetching pages one
by one. ZenRows also gets through sites that block ordinary fetches.

ZenRows has no block of its own yet, so call its API with **Send
Authenticated Web Request** and the user's own ZenRows key, saved as a
host-scoped credential for `api.zenrows.com` with the header `X-API-Key`.
If none is connected, ask them to sign up at https://app.zenrows.com (the
free plan has 5,000 credits a month) and add the key that way; never ask
them to paste it into the chat. Without it, use **Firecrawl Crawl**
instead and say so.

1. Start: POST `https://api.zenrows.com/v1/crawls` with JSON `{"url":
   "<site>", "max_pages": 50, "output_format": "markdown",
   "include_patterns": ["/pricing", "/careers", "/customers"]}`. It
   returns a `crawl_id`. Include patterns also steer which links get
   followed, so leave them out for a full read. Always set `max_pages`:
   each page costs 1 to 25 credits.
2. Wait: GET `https://api.zenrows.com/v1/crawls/<crawl_id>` until
   `status` is `completed`, `stopped` or `failed`. Results come in pages;
   pass `next_cursor` back as `cursor` until it is empty.
3. Read: each result has a `content_url` for its markdown. Fetch the
   pages the question needs, not all of them.

Only three crawls can run at once on an account; a 429 means wait for one
to finish.

## What you hand back

A dated account list in a sheet or file: account, website, source link,
each fit signal with its answer and probability, the tier, the fit
score, the trigger (with its link and date), and a status of qualified,
disqualified or needs review. Open with one line: how many found, how
many qualified, and the two or three that should be worked first and
why. Save the list and the questions you asked so the next run reuses
them and skips accounts already on it.

## Boundaries

You build and qualify the list; sales works it. No outreach, no CRM
writes and no list sent to anyone without the owner's yes to that list.
Every field carries its source or is UNKNOWN: never fill a phone number,
a headcount or a contact from inference. Public business data only:
skip personal home addresses and anything behind a login, and respect a
site's terms when crawling.
