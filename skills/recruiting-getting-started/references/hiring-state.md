# Hiring state: where Harper's files live

The same layout is described in every Harper skill package, because packages
cannot read each other's files. If you change it here, change it there too.

## Why a fixed folder

`write_workspace_file` saves to a session-scoped path by default, so a plan
saved that way is invisible in the next chat. The sandbox folder `~/workspace`
is the durable volume (the expert's own volume in an expert chat) and survives
across chats, delegations and routine runs [114]. It is the record. A copy is
delivered with `write_workspace_file(source_path=...)` so the owner can open
it; the delivered copy is for reading only. Always re-read the `~/workspace`
copy, never the delivered one.

Whether the owner can browse `~/workspace` directly in the UI is unverified,
which is why every deliverable is also delivered as a link.

## Layout

```
~/workspace/hiring/<role-slug>/
  hiring-plan.md          recruiting-getting-started (created), everyone reads
  intake-brief.md         role-intake-and-job-description
  requirements.csv        role-intake-and-job-description (writes),
                          hiring-rubric-design (fills rubric_criterion_id)
  jd-v<N>.md              role-intake-and-job-description
  rubric-v<N>.md          hiring-rubric-design (+ rubric-v<N>.md.sha256 once approved)
  screens/<batch>/        resume-screening
  scorecards/             interview-plan-and-scorecard
  debriefs/               candidate-interview-debrief
  drafts/                 candidate-rejection-email, candidate-offer-draft
```

`<role-slug>` is lowercase letters, digits and hyphens (for example
`billing-ops-lead`). One folder per role; a rescoped role keeps its folder and
bumps `plan_version`.

## Older plans

Before this layout, plans were saved as `hiring-plan-<role>.md` in the cloud
workspace. If `~/workspace/hiring/<role-slug>/` does not exist, look for the
old file with `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`,
read it with `read_workspace_file`, and copy its facts into a new plan.

## If `~/workspace` is not writable

The volume can fail to mount; the box then runs without it [114]. `init_role.sh`
exits 4. Say once that files will not carry to the next chat, keep working in
`/home/user/hiring/<role-slug>/`, and deliver every file with
`write_workspace_file` so the owner has it.

## Memory

- Store only company-level facts: decision-maker, default sender, approvers,
  accommodation route, retention policy, candidate AI-use policy, hiring
  jurisdictions. One fact per `memory_store` call, scope `project:hiring`.
- Never store anything about a candidate.
- A memory hit is a proposal: show it as "from memory, confirm".
- Memory tools are hidden when memory is off; the plan file is then the only record.
- The plan file wins when it and memory disagree; tell the owner about the conflict.
