---
name: "capy-coding-agent"
description: "Hand coding work to a Capy cloud coding agent and see it through: pick the project, write the brief, start the thread, wait for the result, answer its questions, and report the pull request. Also runs Capy pull request reviews. Use when the user wants code written, fixed, or reviewed in a repository their Capy workspace covers."
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
ask them to create one in the Capy app under **Settings → API** and connect
it. Keys can be set to expire; a `capy/Unauthorized` error on a key that used
to work usually means it did, so ask for a fresh one rather than retrying.

Run **Capy List Projects** to see which projects the key reaches and which
repositories each covers. Pick the project whose repositories match the work.
If two could fit, or none lists the repository the user named, say so and ask;
never start a thread in a guessed project. Remember the project ID for the rest
of the conversation.

## Write the brief

The brief is the thread's first message and the agent's only context. Write
it the way you would brief a capable engineer who has never seen this
conversation:

- **Goal**, in one sentence: what should be true when they are done.
- **Where to look**: files, services, error messages, stack traces, issue or
  PR links, and anything the user already ruled out.
- **Done means**: the tests that must pass, the behaviour to verify, and
  whether to open a pull request (say so explicitly, and against which
  branch if not the project's default).
- **Limits**: files or areas not to touch, and anything the user said must not
  change.

Paste the facts the user gave you (the exact error, the reproduction steps);
don't summarise them away. Give the thread a short title so it is easy to find
on the user's Capy board.

New threads run on Muse Spark 1.3 (`meta/muse-spark-1.3`) by default. Keep it
unless the user names another model; then set `model_id` to its Capy ID from
docs.capy.ai/models-and-pricing (for example `openai/gpt-6-astra`), or clear it
to use the project's default. Leave `reasoning` and `machine_size` empty unless
the user asks or the task is unusually heavy. If Capy rejects a model, say
which and why, and ask which model to use instead; don't cycle through guesses.

## Start, wait, report

1. **Capy Create Thread** with the project ID, brief and title. Tell the user
   it has started and give the thread ID.
2. **Capy Wait For Thread** with `timeout_seconds` of 240 or less. A block
   call from chat is cancelled after five minutes, so wait in rounds: if
   `finished` is false, call it again. Between rounds, give the user a
   one-line progress note only when something changed; if they said they'll
   check back later, stop waiting and tell them how to ask for the result.
3. When `finished` is true, read `last_reply`, then act on the status:
   - **needs_you is true**: the agent asked a question. Answer it yourself
     when the conversation already holds the answer; otherwise put the
     question to the user in their words, then send the answer with **Capy
     Send Message**, and go back to step 2.
   - **idle**: the agent delivered. Report what it did and the pull request
     link from its reply. If the reply is a summary without the detail the
     user needs, read more of the transcript with **Capy List Thread
     Messages**.
   - **failed**: say it failed, quote what the transcript shows about why,
     and offer a corrected brief rather than retrying the same one.

Don't paraphrase a pull request as merged or tests as passing unless the
agent's reply says so.

## Steering a thread

- A follow-up ("also cover the empty case", "use the existing helper") goes
  through **Capy Send Message**. The default `interrupt` delivery stops the
  current work and handles the message now; use `steer` to fold it into the
  work in progress, and `queue` to have it wait until the current step ends.
- If the agent is clearly heading the wrong way and spending credits on it,
  **Capy Interrupt Thread** stops it; then send the corrected instruction.
- After any message, wait with **Capy Wait For Thread** again, exactly as for
  a new thread.
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
