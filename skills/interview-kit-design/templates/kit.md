# Interview kit: <Role title>

role_slug: <role-slug>
scale: 1-5
loop_length_note: <e.g. "four slots, one day" or "screen + onsite of three">
accommodation_contact: <name or inbox that handles accommodation requests>
candidate_ai_policy: <owner's stated policy per stage, or UNSET>
status: draft

<!-- Keep the exact line shapes below: scripts/check_kit.py and
     scripts/build_packets.py parse them. One kit per role, saved at
     ~/workspace/hiring/roles/<role-slug>/kit.md -->

## Must-haves

- M1: <must-have exactly as on the role scorecard>
- M2: <...>
- M3: <...>

## Slot 1: <Screen>

length: <minutes, e.g. 30>
interviewer: <name, or UNASSIGNED>
owns: <M-id(s), comma-separated; "none" only for the hiring manager's close>
clock: <5 context, 20 main, 5 candidate questions>   <!-- segments add up to length -->

### Questions

1. "<core question, asked the same way to every candidate>"
   - Strong answer: <what a strong answer shows>
   - Probe: <"Which part was yours?" / "What number moved?" / "What would you change?">
2. "<...>"
   - Strong answer: <...>
   - Probe: <...>
3. "<...>"
   - Strong answer: <...>
   - Probe: <...>
4. "<...>"
   - Strong answer: <...>
   - Probe: <...>

### Anchors M<id>

- 1: <unsatisfactory, in this role's real work>
- 2: <below bar>
- 3: <meets bar>
- 4: <above bar>
- 5: <exceptional>
- not assessed: the slot did not cover it

## Slot 2: <Knockout competency>

length: <...>
interviewer: <...>
owns: <...>
clock: <...>

### Questions

1. "<...>"

### Anchors M<id>

- 1: <...>

## Slot 3: <Deep-dive>

<!-- same shape -->

## Slot 4: <Hiring manager close>

<!-- same shape; owns may be "none" (close and questions) -->

## Dropped or rewritten questions

| Original | Why | Replacement |
| --- | --- | --- |
| <owner's question> | <drop rule or drift, with source> | <rewrite or "dropped"> |

## Open items

- <slot with no interviewer, competency with no owner, anchors still marked draft>
