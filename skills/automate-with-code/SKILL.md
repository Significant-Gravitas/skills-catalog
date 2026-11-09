---
name: automate-with-code
description: Use when a manual, repeated task should become a script or small tool — only where code itself is the deliverable.
version: '1'
---

# Automate with code

Inputs: the manual task steps, input format, expected output, and how often it runs. Output: a tested script or tool with run instructions and a rollback note. Fallbacks: if the task is really a business process to redesign, say so and hand it back — process ownership sits with Operations; build only the coded part.

1. Write the before picture: current steps, time cost if known (label estimates INFERENCE), and error points.
2. Define the contract: exact inputs, exact outputs, idempotency, and what happens on partial failure.
3. Build the smallest thing: one script, the repo's language, no new platform. Secrets via environment variables, never hardcoded.
4. Test on sample and edge inputs; make it safe to re-run. Destructive actions need a dry-run mode and the owner's yes.
5. Pilot with rollback: run it alongside the manual way once, compare outputs, then hand over.
6. Deliver the four-part contract plus run instructions a non-author can follow.

<!-- Reuse: pilot-with-rollback automation discipline, narrowed to code-as-deliverable scope. -->
