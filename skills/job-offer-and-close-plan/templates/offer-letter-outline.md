# Offer letter outline (structure only - not binding wording)

Use this only to check that a company template covers everything, or to
show the owner what their template is missing. **Binding wording comes from
the company's own template.** If the owner has no template, every clause
below stays `[COMPANY TEMPLATE REQUIRED]` and the draft goes to the attorney
with templates/attorney-brief.md. Never write employment terms, tax, equity,
benefits, immigration or at-will/notice language from scratch.

Placeholders use `{{key}}` so `scripts/fill_offer_template.py` can fill them.

---

{{entity}}

Dear {{candidate_first_name}},

We are pleased to offer you the position of {{title}} ({{level}}), a
{{position_type}} role reporting to {{manager}}, based {{location}}
({{work_terms}}).

- Start date: {{start_date}}
- Base pay: {{currency}} {{base_pay}} per {{pay_period}}
- Bonus: {{bonus_text}}
- Sales roles only - on-target earnings {{currency}} {{ote}} ({{currency}} {{variable_target}} variable at target), under the commission plan: {{commission_plan_text}}; ramp: {{ramp_text}}
- Equity: {{equity_text}}
- Signing bonus: {{currency}} {{signing}}
- Benefits: as described in {{benefits_source}}
- Probation: {{probation}}

Conditions: [COMPANY TEMPLATE REQUIRED - contingencies in the template's own
order; see references/contingency-order.md]

This offer is open until {{response_by}}. Questions: {{contact_for_questions}}.

[COMPANY TEMPLATE REQUIRED - governing terms, at-will or notice language,
entire-agreement clause, signature block]

{{signatory}}
