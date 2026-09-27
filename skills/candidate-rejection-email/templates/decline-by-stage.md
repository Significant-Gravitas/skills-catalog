# Decline templates by stage

`scripts/merge_declines.py` reads the blocks between the `template:` markers,
so keep the markers and `{{placeholders}}` intact when editing. Everything
outside the markers is guidance for the model.

Rules that apply to every stage:
- The decision appears in the first two sentences.
- The thanks name the specific time or work the candidate gave.
- `{{feedback_paragraph}}` is filled only from feedback the decision-maker
  approved word for word. Otherwise it is empty; never write a generic reason.
- `{{retention_paragraph}}` is filled only with the owner's recorded retention
  wording. Otherwise it is empty; never write "we'll keep your details on file" [100].
- `{{expenses_paragraph}}` is filled only for late-stage candidates with
  expenses or work-sample handling, using the approved contact and date.
- No comparison with other candidates, no mention of AI, scores or how the
  decision was made, and no promise of future contact.
- The subject stays plain: "Your application for <role>".

Placeholders: `chosen_name`, `role`, `company`, `thanks_detail`,
`feedback_paragraph`, `retention_paragraph`, `expenses_paragraph`, `sender`,
`sender_title`.

---

## Application stage (no interview)

Short. No feedback unless approved; at this volume it rarely is.

<!-- template:application -->
Subject: Your application for {{role}}

Hi {{chosen_name}},

Thank you for applying for the {{role}} role at {{company}}{{thanks_detail}}. We have decided not to move forward with your application.

{{feedback_paragraph}}{{retention_paragraph}}Thank you again for your interest in {{company}}, and best wishes with your search.

{{sender}}
{{sender_title}}
<!-- /template -->

## After a screen (recruiter or hiring-manager call)

<!-- template:screen -->
Subject: Your application for {{role}}

Hi {{chosen_name}},

Thank you for your time{{thanks_detail}}. The team has decided not to move forward with your application.

{{feedback_paragraph}}{{retention_paragraph}}Thank you again, and best wishes.

{{sender}}
{{sender_title}}
<!-- /template -->

## After the interview loop (email version)

Late-stage candidates gave the most time, so the owner may prefer a call
first (talking points below), followed by this email.

<!-- template:loop -->
Subject: Your application for {{role}}

Hi {{chosen_name}},

Thank you for interviewing for the {{role}} role{{thanks_detail}}. The team has decided not to move forward with your application.

{{feedback_paragraph}}{{expenses_paragraph}}{{retention_paragraph}}Thank you again for the time and care you put into the process, and best wishes.

{{sender}}
{{sender_title}}
<!-- /template -->

## After the interview loop: talking points for a call (not mail-merged)

For the sender, not the candidate. Keep the call short and kind.

1. Open with the decision in the first sentence or two: "I'm calling about the <role> role. I'm sorry to say we've decided not to move forward."
2. Thank them for the specific work: "<the SQL work sample / the three interviews>."
3. If feedback was approved, read it as approved and add nothing: "<approved text>." If none was approved: "I'm not able to share detailed feedback, but I wanted you to hear it from me."
4. Do not debate the decision, compare them with other candidates, or describe how the panel scored.
5. Practicalities: "<expenses: send receipts to <contact> by <date>>" / "<work sample: we'll delete your submission by <date> / as our policy states>."
6. Close: "Thank you again. I'll follow up with a short email."
7. Then send (the sender, not Harper) the loop email above.

## Consumer report or background check involved

No template. Draft nothing. See `references/fcra-adverse-action-routing.md`.
