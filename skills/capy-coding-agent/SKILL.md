---
name: "capy-coding-agent"
description: "Hand coding work to Capy, an AI software engineer that runs background coding agents in the cloud, and see it through: pick the project, write the brief, start the thread, wait for the result, answer its questions, and report the pull request. Also runs Capy pull request reviews. Use when the user wants code written, fixed, or reviewed in a repository their Capy workspace covers."
triggers: ["capy", "have capy fix this", "open a pull request for this", "fix this bug in the repo", "write the code for this", "delegate this to a coding agent", "review this pull request", "what is capy working on", "check on the capy thread", "how much has capy spent"]
version: "1"
---

# Capy coding agent

Capy runs coding agents on cloud machines against the user's GitHub
repositories. Each piece of work is a **thread**: you brief it once, the agent
works (reading code, running tests, pushing a branch, opening a pull request),
and then it replies. You drive it with the Capy blocks. The run bills the
user's Capy organization, not the platform.

Use Capy when the job is code in a repository: a bug fix, a feature, a
refactor, a dependency upgrade, a test gap, or "look into why this fails". For
a question you can answer by reading, or code you can write and run in your
own sandbox, do that instead; don't start an agent for it.

## Before the first thread

The blocks need the user's Capy API key. If no Capy credential is connected,
ask them to create one at https://capy.ai/settings/api and connect it. Keys
can be set to expire; a `capy/Unauthorized` error on a key that used to work
usually means it did, so ask for a fresh one rather than retrying.

Run **Capy List Projects** to see which projects the key reaches and which
repositories each covers. Pick the project whose repositories match the work.
If two could fit, or none lists the repository the user named, say so and ask;
never start a thread in a guessed project. Remember the project ID for the rest
of the conversation.

If the key reaches no project, or none covers the repository, the user has to
fix that in Capy: create a project at https://capy.ai and install the Capy
GitHub App on the repository. The blocks can't do either for them.

### A project Capy hasn't worked in yet

An agent that can't install the dependencies and run the tests guesses, and
the user finds out in CI. Capy fixes that with the project's dev environment:
setup scripts, the processes to start, named test commands, and a snapshot
so machines boot ready. When **Capy List Threads** shows the project has no
threads yet, open the first brief with: "First, check this project's dev
environment. If the setup can't install dependencies and run the tests, set
it up (setup scripts and a test command), verify it on your machine, and
enable snapshots. Then do the task." Tell the user you did, and give them the
project's `dev_environment_url` to review what it set up.

### Secrets

Never ask the user to paste a secret into this chat. When the agent needs a
value (an API key, a `DATABASE_URL`), send the user to the project's
`environment_variables_url` to set it once for every thread, or to the
thread's own page (`thread_url`) to hand it to that thread alone. Then tell
the agent the value is set and to carry on. The agent sees variable names,
never values.

## Is it worth sending?

Before briefing an agent on a bug, spend a minute confirming there is still
something to fix. Read the failing code on the branch the fix would target:
an error report can come from an old build or someone's stale local checkout,
and the fix may already be merged. Check for an open pull request that already
covers it. If it is already fixed, say so and close the ticket instead of
starting a thread. When the root cause is clear, put it in the brief; the
agent works faster from a diagnosis than from a symptom.

## Write the brief

The brief is the thread's first message and the agent's only context. Write
it the way you would brief a capable engineer who has never seen this
conversation:

- **Goal**, in one sentence: what should be true when they are done.
- **Where to look**: files, services, error messages, stack traces, issue or
  PR links, and anything the user already ruled out.
- **Done means**: the tests that must pass, the behaviour to verify, and
  whether to open a pull request. Name the target branch every time: the
  project's base branch is often the release branch, not the one pull
  requests go to (the repository's contributing guide says which).
- **Ticket**: when the work came from a tracked issue (Sentry, Linear,
  GitHub), link it and ask for its closing keyword in the commit message and
  pull request body (for example `Fixes AUTOGPT-SERVER-5E4`), so the tracker
  closes it when the fix ships.
- **Limits**: files or areas not to touch, and anything the user said must not
  change.

Paste the facts the user gave you (the exact error, the reproduction steps);
don't summarise them away. Give the thread a short title so it is easy to find
on the user's Capy board.

## Choose the model and who pays

Leave `model_id` empty to use the default model the user set in Capy. When
they want the strongest agent for real engineering work, use
`claude-opus-5-5`, or, when a ChatGPT subscription is linked in Capy, a GPT
model on the `codex` route. When the user names a model, set `model_id` to its name
(for example `gpt-6-astra`, `claude-opus-5-5`, `grok-4.5`) and pick who pays
with `model_route`:

- `capy_balance` bills the organization's Capy balance.
- `codex`, `copilot`, `supergrok` or `azure` run the model through that
  provider linked in Capy's settings (a ChatGPT, GitHub Copilot or SuperGrok
  subscription, or an Azure organization account), so the tokens bill the
  subscription instead.

When the user says to use their subscription ("run it on my Codex"), use that
route. When they don't say, and the conversation shows they have a
subscription linked in Capy, prefer it over the balance. Not every model is
offered on every route (docs.capy.ai/models-and-pricing lists them).

A rejected model starts nothing and costs nothing, so trying a route is safe.
If the linked provider is disconnected or was never linked, the error says
which. Tell the user to reconnect or link it in Capy under Settings > Models,
and ask whether to run on the Capy balance meanwhile. Set
`fall_back_to_capy_balance` only when the user has said the balance may pay,
since it moves the cost off their subscription. For an unknown model, say so
and ask which to use; don't cycle through guesses.

When you report a result, include `billed_via` from Capy Wait For Thread
when the user cares who paid.

Leave `reasoning` and `machine_size` empty unless the user asks or the task is
unusually heavy.

## Hand off, then follow up

1. **Capy Create Thread** with the project ID, brief and title. Tell the user
   it has started in one or two lines: what you asked for, and the
   `thread_url`, where they can watch the agent's plan, commands and diff
   live.
2. Decide how to wait. A block call from chat is cancelled after five
   minutes, so **Capy Wait For Thread** runs in rounds of `timeout_seconds`
   240 or less; if `finished` is false, call it again.
   - Quick work (a question about the code, a one-file fix): wait in rounds
     now. Between rounds, add a one-line note only when something changed.
   - Anything longer (a feature, a multi-file fix, anything that goes through
     CI): don't hold the chat. Tell the user you'll report back, then
     schedule a follow-up in this conversation (`schedule_followup` with this
     chat's session id, about 15 minutes out) that runs one Wait For Thread
     round. If it isn't finished, schedule the next follow-up; when it is,
     report.
3. When `finished` is true, read `last_reply`, then act on the status:
   - **needs_you is true**: the agent asked a question. Answer it yourself
     when the conversation already holds the answer; otherwise put the
     question to the user in their words, then send the answer with **Capy
     Send Message**, and go back to step 2.
   - **idle**: the agent delivered. Report what it did, the pull request
     (`pull_request_url`, found from its replies) and the `thread_url`. If
     the reply is a summary without the detail the user needs, read more of
     the transcript with **Capy List Thread Messages**; pass its
     `older_cursor` back as `before_cursor` to go further back.
   - **failed**: say it failed, quote what the transcript shows about why,
     and offer a corrected brief rather than retrying the same one.

Don't paraphrase a pull request as merged or tests as passing unless the
agent's reply says so.

## After the pull request opens

Capy follows its own pull request. A failing check wakes the thread, and the
agent reads the job, fixes it and pushes again. Review comments reach the
thread and it answers them. The merge wakes it to wrap up. So a thread that
goes back to `working` or `waiting` after the pull request opened is usually
handling CI or a review: let it, and don't run a CI loop of your own.

Your part is what Capy can't do for the user:

1. **Read the diff** with the GitHub pull request blocks before you call it
   done, and check it against the brief: does it fix the root cause, and does
   it weaken anything? For example, dropping validation on data a user can
   write is a security regression, even when it silences the error. Send
   anything wrong back to the same thread with **Capy Send Message**; the agent
   keeps its branch and context. For a risky change, also check it out in
   your own sandbox (`gh pr checkout`) and run the tests the brief named.
2. **Watch for the merge.** Merging is the repository owner's call; merge only
   when the user asks you to. Reviews can take hours or days, so don't wait
   in chat. Schedule a follow-up in this conversation (`schedule_followup`
   with this chat's session id, a few hours out) that reads the pull request
   with the GitHub Read Pull Request block. If `merged` is true, close the
   loop. If the PR is still open, schedule the next check. If it was closed
   without merging, tell the user. Chain one-off follow-ups rather than a
   repeating one, so nothing keeps firing after the PR is done.
3. **Close the loop** when it merges. Mark the ticket it came from: for a
   Sentry issue use `resolvedInNextRelease`, because a merge to a development
   branch is not yet running in production. Then tell the user, and archive
   the Capy thread.

When this is standing work rather than one ticket (for example "every morning,
triage new Sentry errors and send the fixable ones to Capy"), set it up as a
routine (`schedule_routine`), so it has its own thread that remembers which
tickets it already sent.

## Steering a thread

- A follow-up ("also cover the empty case", "use the existing helper") goes
  through **Capy Send Message**. The default `interrupt` delivery stops the
  current work and handles the message now; use `steer` to fold it into the
  work in progress, and `queue` to have it wait until the current step ends.
- To move a thread to another model or payer, send the next message with
  `model_id` and `model_route` set; the thread keeps its context.
- If the agent is clearly heading the wrong way and spending credits on it,
  **Capy Interrupt Thread** stops it; then send the corrected instruction.
- After any message, wait with **Capy Wait For Thread** again, exactly as for
  a new thread, and pass Send Message's `message_id` as `after_message_id`.
  The wait then ends on the reply to your message, not the agent's previous
  one, which matters most with `queue` delivery.
- **Capy List Thread Tasks** shows how a big thread split its work across
  subagents and what each part spent. Tasks are read-only; steer them through
  the thread.
- **Capy Archive Thread** takes a finished thread off the board. Do it when
  the user is done with the work, not while a pull request is still in
  review.

Keep one thread per piece of work, and send follow-ups to the same thread
rather than starting a new one: the agent keeps its context, its machine and
its branch. **Capy List Threads** finds an earlier thread when the user refers
to one ("the Node upgrade Capy did last week").

## Pull request reviews

**Capy Start Review** runs Capy's reviewer on a GitHub pull request in a
repository the organization's Capy GitHub installation covers. The reviewer
reads the diff in a real checkout and posts its findings as inline comments on
the pull request, so they are visible to everyone on it.

- Asking again for the same commits returns the existing round (`adopted` is
  true) and costs nothing. Use `force_refresh` only when the user explicitly
  wants a completed round re-run.
- Leave `tier` empty for the repository's default. `high` is a deeper, more
  expensive review; use it when the user asks for a thorough one.
- If the pull request was opened by a Capy thread, pass that thread's ID as
  `source_thread_id`: the verdict goes to the thread, and the agent triages
  the findings and fixes the serious ones itself.
- Read the result with **Capy Get Review Round** using the returned
  `request_id`. Poll until `is_settled` is true, then report the
  high-severity issues first with their file and line, then the rest briefly.
  A round that settles as `failed` or `stale` reviewed nothing: say so, and
  never report it as a clean review.
  Confirmed findings are proven by the diff; investigate findings are risks
  to check, so say which is which.
- A closed or draft pull request, or one Capy can't read, is refused with a
  reason. Pass the reason on.

## Spend

Threads and reviews bill the user's Capy organization in credits.
**Capy Get Usage** reports dollars spent for a date range (the current month
by default), broken down by member and model, and each thread's `usage` shows
its own credits. When the user sets a budget, check it before starting new
work and tell them when a thread is running long.

## Errors

The blocks name Capy's error: `capy/Forbidden` means the key's principal
isn't allowed this (a read-only service key, or a project outside its
access); `capy/ProjectNotFound` and `capy/ThreadNotFound` mean the ID isn't
visible to this key; `capy/RateLimited` gives the seconds to wait;
`capy/PaidFeatureUnavailable` means the organization's plan doesn't include
that option (such as the largest machine size). Report the cause in plain
words and what would fix it; don't loop on the same call.
