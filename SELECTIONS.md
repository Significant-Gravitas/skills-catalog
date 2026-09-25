# Installed selections

This document reviews the 74 replacement packages proposed in PR 4. The catalog
also retains 166 unchanged additions from Nick's PR 2, bringing the draft to
240 entries. Those retained packages are not new upstream selections. The
shared-name choice remains open; see [the retention rule](docs/PR2_RETENTION.md).

74 unique skill packages; original authors retain authorship. Clear names, source metadata and necessary local reference changes are packaging adaptations only. Every package has an exact upstream licence and attribution.

Status: 10 conditional, 64 core. Conditional packages require the recorded services/native behavior before enabling them. All packages remain untested at runtime.

Usage/activity observations were captured on 2026-09-24/25. Installs are telemetry, repository stars are repository-wide, and neither proves successful outputs. Companion evidence is qualified separately. Full raw responses are retained under provenance/evidence-files.

[Every expert and original assignment](docs/EXPERT_COVERAGE.md) · [40 deferred sources](docs/DEFERRED_SKILLS.md) · [Runtime requirements](docs/IMPORT_COMPATIBILITY.md)

## account-reconciliation

Reconcile bank and ledger balances,explain differences and track unresolved items.

- Original: **reconciliation**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/finance/skills/reconciliation/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/reconciliation).
- Licence: Apache-2.0; [full text](skills/account-reconciliation/LICENSE). Status: core.
- Experts: Daniel, Mina.
- Evidence: Installs (skills.sh displayed count; installations, not unique users): 3.2K; GitHub repository stargazers_count (repository-wide, not candidate-specific use): 25533; GitHub repository pushed_at (repository-wide, not proof this skill was recently edited): 2026-09-24T07:36:14Z; Weekly installs (8 displayed buckets, dates not exposed in label; same skills.sh telemetry source): 105, 88, 110, 81, 74, 65, 88, 84
- [Source, usage evidence, requirements and recorded review](provenance/skills/account-reconciliation.json).

## board-deck-builder

Build investor and board update decks with metrics,risks,forecasts and specific asks.

- Original: **board-deck-builder**, by **Alireza Rezvani**. [Pinned source](https://github.com/alirezarezvani/claude-skills/blob/19392f7a08264ed00486a251f5b2098321771f94/c-level-advisor/skills/board-deck-builder/SKILL.md) · [discovery](https://skills.sh/alirezarezvani/claude-skills/board-deck-builder).
- Licence: MIT; [full text](skills/board-deck-builder/LICENSE). Status: core.
- Experts: Daniel, Theo.
- Evidence: Installs (skills.sh displayed count; installations, not unique users): 603; GitHub repository stargazers_count (repository-wide, not candidate-specific use): 26392; GitHub repository pushed_at (repository-wide, not proof this skill was recently edited): 2026-08-30T09:46:16Z; Weekly installs (8 displayed buckets, dates not exposed in label; same skills.sh telemetry source): 3, 3, 7, 2, 6, 5, 5, 2
- [Source, usage evidence, requirements and recorded review](provenance/skills/board-deck-builder.json).
- Evidence qualification: Lower-adoption specialist selection: 603 installs. Publisher/repository evidence and substantive source review support selection, but individual uptake is smaller and effectiveness is not independently proven.

## business-process-documentation

Turn a process walkthrough into an SOP with scope, roles, steps, handoffs, exceptions, metrics and ownership.

- Original: **process-doc**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/operations/skills/process-doc/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/process-doc).
- Licence: Apache-2.0; [full text](skills/business-process-documentation/LICENSE). Status: core.
- Experts: James.
- Evidence: individual-installs: 2.7K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/business-process-documentation.json).

## business-process-optimization

Map current work, locate delay/rework/manual handoffs, propose a simpler future state and track before-and-after improvements.

- Original: **process-optimization**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/operations/skills/process-optimization/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/process-optimization).
- Licence: Apache-2.0; [full text](skills/business-process-optimization/LICENSE). Status: core.
- Experts: James.
- Evidence: individual-installs: 3.0K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/business-process-optimization.json).

## candidate-interview-planning

Build competency-based interview questions, panel assignments, anchored scorecards and a structured debrief template.

- Original: **interview-prep**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/human-resources/skills/interview-prep/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/interview-prep).
- Licence: Apache-2.0; [full text](skills/candidate-interview-planning/LICENSE). Status: core.
- Experts: Harper, Sofia.
- Evidence: Installs (skills.sh visible label; not unique users): 3.5K; GitHub stargazers_count (repository-wide, not individual-skill use): 25533; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-09-24T07:36:14Z; Latest commit touching exact SKILL.md at pinned revision: 2026-02-24T00:08:12Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/candidate-interview-planning.json).

## client-proposal-writing

Turn discovery notes, scope, pricing and timelines into a clear client proposal or service SOW draft.

- Original: **proposal-writer**, by **Jeremy Dawes (Jezweb) and upstream contributors**. [Pinned source](https://github.com/jezweb/claude-skills/blob/e875a6bfff809e5d42c584104031e36e1f014f18/plugins/writing/skills/proposal-writer/SKILL.md) · [discovery](https://skills.sh/jezweb/claude-skills/proposal-writer).
- Licence: MIT; [full text](skills/client-proposal-writing/LICENSE). Status: core.
- Experts: Jordan, Max.
- Evidence: Installs (skills.sh visible label; not unique users): 1.1K; GitHub stargazers_count (repository-wide, not individual-skill use): 1025; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-07-02T07:34:37Z; Maintainer public source audit explicitly lists proposal-writer (not independent user adoption): Issue #90 records a whole-skill audit and proposal-writer description update.
- [Source, usage evidence, requirements and recorded review](provenance/skills/client-proposal-writing.json).

## code-change-security-review

Review a proposed code change for weakened safeguards, regressions, affected callers, test gaps and concrete security consequences.

- Original: **differential-review**, by **Omar Inuwa; published by Trail of Bits**. [Pinned source](https://github.com/trailofbits/skills/blob/32e34f8173796e3566a51aee877dc96bc5191f64/plugins/differential-review/skills/differential-review/SKILL.md) · [discovery](https://www.skills.sh/trailofbits/skills/differential-review).
- Licence: CC-BY-SA-4.0; [full text](skills/code-change-security-review/LICENSE). Status: core.
- Experts: Devon.
- Evidence: Installs (skills.sh displayed cumulative count, rounded where K is shown; not unique users): 6.9K; GitHub stargazers_count (repository-level, not skill usage): 7,226; Repository pushed_at (not individual skill revision): 2026-09-23T16:36:04Z; Most recent commit touching candidate directory (metadata changes may account for activity): 2026-09-16T22:05:09Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/code-change-security-review.json).

## code-review-quality

Review a pull request for correctness, security, performance, test quality and maintainability, then give prioritized, constructive feedback.

- Original: **code-review-excellence**, by **Seth Hobson**. [Pinned source](https://github.com/wshobson/agents/blob/4236bb91f8395b0435f1d8b8baf9e8e4c69a8620/plugins/developer-essentials/skills/code-review-excellence/SKILL.md) · [discovery](https://www.skills.sh/wshobson/agents/code-review-excellence).
- Licence: MIT; [full text](skills/code-review-quality/LICENSE). Status: core.
- Experts: Casey.
- Evidence: individual-installs: 28.8K installs displayed; repo-stars: 39930; maintenance: Latest repository commit observed: 4236bb91f8395b0435f1d8b8baf9e8e4c69a8620 at 2026-09-13T14:43:53Z; ci: rebuild the Claude Code review workflow from scratch (#708); maintenance: Selected path latest change on or before pin: 47a5dbc3f9c2661c6afb13638f80d4a4d4449040 at 2026-03-07T15:53:17Z; fix(skills): remove phantom resource references and fix CoC links (#447)
- [Source, usage evidence, requirements and recorded review](provenance/skills/code-review-quality.json).

## company-policy-lookup

Find and explain the relevant company HR policy with citations, examples and escalation for unclear or exceptional cases.

- Original: **policy-lookup**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/human-resources/skills/policy-lookup/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/policy-lookup).
- Licence: Apache-2.0; [full text](skills/company-policy-lookup/LICENSE). Status: core.
- Experts: Ines.
- Evidence: individual-installs: 2.7K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/company-policy-lookup.json).

## competitor-profiling

Build evidence-backed competitor profiles and strategic implications.

- Original: **competitor-profiling**, by **Corey Haines / contributors; retain upstream copyright and notices.**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/competitor-profiling/SKILL.md) · [discovery](https://www.skills.sh/coreyhaines31/marketingskills/competitor-profiling).
- Licence: MIT; [full text](skills/competitor-profiling/LICENSE). Status: conditional.
- Experts: Alex, Nadia, Zara.
- Evidence: skills.sh displayed installs (rounded where shown): 78.3K; GitHub repository stars, not individual skill users: 51391; Pinned repository last commit date (not per-skill): 2026-09-05T04:48:02Z; User reproduces broken support links in installed emails/churn-prevention copies; says v2 improved. Repository/package evidence, not endorsement of all skills.: Issue #524, installed copies dated 2026-08-16; unresolved portable-file issue
- [Source, usage evidence, requirements and recorded review](provenance/skills/competitor-profiling.json).

## compliance-evidence-tracking

Organize framework requirements, control owners, evidence, audit dates, gaps and remediation tracking.

- Original: **compliance-tracking**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/operations/skills/compliance-tracking/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/compliance-tracking).
- Licence: Apache-2.0; [full text](skills/compliance-evidence-tracking/LICENSE). Status: core.
- Experts: James, Lena.
- Evidence: individual-installs: 2.8K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/compliance-evidence-tracking.json).

## contract-amendment-history

Trace contract changes and exact clause versions across a base agreement and its amendments.

- Original: **amendment-history**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/claude-for-legal/blob/4a6c651889c97cc9140580363c73e0eb17379c2b/commercial-legal/skills/amendment-history/SKILL.md) · [discovery](https://skills.sh/anthropics/claude-for-legal/amendment-history).
- Licence: Apache-2.0; [full text](skills/contract-amendment-history/LICENSE). Status: core.
- Experts: Ellis.
- Evidence: Installs (skills.sh visible label; not unique users): 566; GitHub stargazers_count (repository-wide, not individual-skill use): 9516; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-09-24T11:06:40Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/contract-amendment-history.json).
- Evidence qualification: Lower-adoption specialist selection: 566 installs. Publisher/repository evidence and substantive source review support selection, but individual uptake is smaller and effectiveness is not independently proven.

## conversion-rate-optimization

Review landing pages and forms for message match, clear value, calls to action, credible proof and friction, then prioritize improvements and tests.

- Original: **cro**, by **Corey Haines**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/cro/SKILL.md) · [discovery](https://skills.sh/coreyhaines31/marketingskills/cro).
- Licence: MIT; [full text](skills/conversion-rate-optimization/LICENSE). Status: core.
- Experts: Marco.
- Evidence: individual-installs: 71.7K all-time installs displayed; repo-stars: 51420; maintenance: Current pinned repository commit 5b2c0007766c6a1cf1d53fd8fc73e979e0821022 dated 2026-09-05T04:48:02Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/conversion-rate-optimization.json).

## customer-escalation

Prepare actionable escalations and maintain customer follow-up.

- Original: **customer-escalation**, by **Anthropic / upstream contributors; retain Apache-2.0 and applicable notices.**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/customer-support/skills/customer-escalation/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/customer-escalation).
- Licence: Apache-2.0; [full text](skills/customer-escalation/LICENSE). Status: core.
- Experts: Riley, Robin, Sasha.
- Evidence: skills.sh displayed cumulative install telemetry, not active users: 2.7K; GitHub stargazers_count (repository-level, not skill usage): 25,533; Repository pushed_at (not individual skill revision): 2026-09-24T07:36:14Z; Captured customer-support path history, not a claim of every-file revision date: Upstream commit history saved
- [Source, usage evidence, requirements and recorded review](provenance/skills/customer-escalation.json).

## customer-insight-research

Turn interviews, support tickets, surveys and public reviews into sourced customer insights.

- Original: **customer-research**, by **Corey Haines / contributors; retain upstream copyright and notices.**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/customer-research/SKILL.md) · [discovery](https://www.skills.sh/coreyhaines31/marketingskills/customer-research).
- Licence: MIT; [full text](skills/customer-insight-research/LICENSE). Status: core.
- Experts: Alex, Max, Nadia, Priya, Riley.
- Evidence: skills.sh displayed cumulative install telemetry, not active users: 98.2K; GitHub repository stars, not individual skill users: 51391; Pinned repository last commit date (not per-skill): 2026-09-05T04:48:02Z; User reproduces broken support links in installed emails/churn-prevention copies; says v2 improved. Repository/package evidence, not endorsement of all skills.: Issue #524, installed copies dated 2026-08-16; unresolved portable-file issue
- [Source, usage evidence, requirements and recorded review](provenance/skills/customer-insight-research.json).

## customer-response-drafting

Draft account updates and sensitive customer replies.

- Original: **draft-response**, by **Anthropic / upstream contributors; retain Apache-2.0 and applicable notices.**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/customer-support/skills/draft-response/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/draft-response).
- Licence: Apache-2.0; [full text](skills/customer-response-drafting/LICENSE). Status: core.
- Experts: Riley, Robin, Sasha.
- Evidence: skills.sh displayed cumulative install telemetry, not active users: 2.6K; GitHub stargazers_count (repository-level, not skill usage): 25,533; Repository pushed_at (not individual skill revision): 2026-09-24T07:36:14Z; Captured customer-support path history, not a claim of every-file revision date: Upstream commit history saved
- [Source, usage evidence, requirements and recorded review](provenance/skills/customer-response-drafting.json).

## customer-support-research

Research account history, product questions and prior commitments with source attribution.

- Original: **customer-research**, by **Anthropic / upstream contributors; retain Apache-2.0 and applicable notices.**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/customer-support/skills/customer-research/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/customer-research).
- Licence: Apache-2.0; [full text](skills/customer-support-research/LICENSE). Status: core.
- Experts: Riley, Robin, Sasha.
- Evidence: skills.sh displayed cumulative install telemetry, not active users: 2.9K; GitHub stargazers_count (repository-level, not skill usage): 25,533; Repository pushed_at (not individual skill revision): 2026-09-24T07:36:14Z; Captured customer-support path history, not a claim of every-file revision date: Upstream commit history saved
- [Source, usage evidence, requirements and recorded review](provenance/skills/customer-support-research.json).

## data-visualization

Turn prepared results into suitable, clearly labeled static or interactive charts with accessible presentation.

- Original: **data-visualization**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/data/skills/data-visualization/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/data-visualization).
- Licence: Apache-2.0; [full text](skills/data-visualization/LICENSE). Status: core.
- Experts: Quinn.
- Evidence: Installs (skills.sh displayed cumulative count, rounded; not unique users): 12.3K; GitHub stargazers_count (repository-level, not skill usage): 25,533; Repository pushed_at (not individual skill revision): 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/data-visualization.json).

## dataset-exploration

Understand a dataset before relying on it: profile its grain, keys, missing values, distributions, date coverage and useful relationships.

- Original: **explore-data**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/data/skills/explore-data/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/explore-data).
- Licence: Apache-2.0; [full text](skills/dataset-exploration/LICENSE). Status: core.
- Experts: Omar, Quinn.
- Evidence: Installs (skills.sh displayed cumulative count, rounded where K is shown; not unique users): 5.6K; GitHub stargazers_count (repository-level, not skill usage): 25,533; Repository pushed_at (not individual skill revision): 2026-09-24T07:36:14Z; Most recent commit touching candidate directory (metadata changes may account for activity): 2026-03-13T15:57:57Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/dataset-exploration.json).

## employee-onboarding-planning

Create a role-specific first-day, first-week and 30/60/90-day onboarding plan covering access, people, goals and check-ins.

- Original: **onboarding**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/human-resources/skills/onboarding/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/onboarding).
- Licence: Apache-2.0; [full text](skills/employee-onboarding-planning/LICENSE). Status: core.
- Experts: Ines.
- Evidence: individual-installs: 2.6K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/employee-onboarding-planning.json).

## employee-performance-review

Prepare self-assessments, manager reviews and calibration materials grounded in goals, examples, competencies and development plans.

- Original: **performance-review**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/human-resources/skills/performance-review/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/performance-review).
- Licence: Apache-2.0; [full text](skills/employee-performance-review/LICENSE). Status: core.
- Experts: Ines.
- Evidence: individual-installs: 3.1K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/employee-performance-review.json).

## employment-offer-drafting

Draft an offer letter, compensation package and hiring-manager negotiation notes using role, location, compensation and start-date inputs.

- Original: **draft-offer**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/human-resources/skills/draft-offer/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/draft-offer).
- Licence: Apache-2.0; [full text](skills/employment-offer-drafting/LICENSE). Status: core.
- Experts: Harper, Sofia.
- Evidence: Installs (skills.sh visible label; not unique users): 2.5K; GitHub stargazers_count (repository-wide, not individual-skill use): 25533; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-09-24T07:36:14Z; individual-installs: 2.5K
- [Source, usage evidence, requirements and recorded review](provenance/skills/employment-offer-drafting.json).

## financial-statement-preparation

Prepare comparative income statements,financial metrics and supported movement commentary.

- Original: **financial-statements**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/finance/skills/financial-statements/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/financial-statements).
- Licence: Apache-2.0; [full text](skills/financial-statement-preparation/LICENSE). Status: core.
- Experts: Daniel, Mina, Theo.
- Evidence: Installs (skills.sh displayed count; installations, not unique users): 4.1K; GitHub repository stargazers_count (repository-wide, not candidate-specific use): 25533; GitHub repository pushed_at (repository-wide, not proof this skill was recently edited): 2026-09-24T07:36:14Z; Weekly installs (8 displayed buckets, dates not exposed in label; same skills.sh telemetry source): 139, 108, 110, 92, 90, 72, 78, 98
- [Source, usage evidence, requirements and recorded review](provenance/skills/financial-statement-preparation.json).

## go-to-market-strategy

Develop a market-entry or launch strategy connecting audience research, channel choice, messaging, success metrics and a phased execution roadmap.

- Original: **gtm-strategy**, by **Paweł Huryn**. [Pinned source](https://github.com/phuryn/pm-skills/blob/8607e3b077817f89bf4a9b623246219734ac3be0/pm-go-to-market/skills/gtm-strategy/SKILL.md) · [discovery](https://skills.sh/phuryn/pm-skills/gtm-strategy).
- Licence: MIT; [full text](skills/go-to-market-strategy/LICENSE). Status: core.
- Experts: Max, Zara.
- Evidence: individual-installs: 2.9K all-time installs displayed; repo-stars: 26581; maintenance: Current pinned commit 8607e3b077817f89bf4a9b623246219734ac3be0 at 2026-09-14T21:15:01Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/go-to-market-strategy.json).

## knowledge-base-article-writing

Turn a resolved case or recurring question into a searchable help article, FAQ, troubleshooting guide or known-issue document.

- Original: **kb-article**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/customer-support/skills/kb-article/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/kb-article).
- Licence: Apache-2.0; [full text](skills/knowledge-base-article-writing/LICENSE). Status: core.
- Experts: Robin, Sasha.
- Evidence: individual-installs: 2.7K installs displayed; repo-stars: 25556; maintenance: Latest repository commit observed: da38ec1ee89d41e5380e652a97382695003396e7 at 2026-09-24T19:33:00Z; adobe-for-creativity: display name "Adobe" (#1245); maintenance: Selected path latest change on or before pin: 2d6f7e22dd25593f0f748010430ef86f19659735 at 2026-03-13T15:57:57Z; Migrate commands to skills across all plugins
- [Source, usage evidence, requirements and recorded review](provenance/skills/knowledge-base-article-writing.json).

## legal-meeting-briefing

Prepare legal/contract/vendor/board meeting briefs and action follow-up when Frankie is supporting an in-house legal team.

- Original: **meeting-briefing**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/legal/skills/meeting-briefing/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/meeting-briefing).
- Licence: Apache-2.0; [full text](skills/legal-meeting-briefing/LICENSE). Status: conditional.
- Experts: Frankie.
- Evidence: Installs (skills.sh displayed installations,not unique users): 2.8K; GitHub stargazers_count; repository-wide popularity,not individual skill use: 25533; Repository pushed_at; not per-skill latest edit: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/legal-meeting-briefing.json).

## legal-response-drafting

Draft routine legal responses from approved templates and company context, screening escalation triggers before producing a response.

- Original: **legal-response**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/legal/skills/legal-response/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/legal-response).
- Licence: Apache-2.0; [full text](skills/legal-response-drafting/LICENSE). Status: core.
- Experts: Lena.
- Evidence: individual-installs: 3.2K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/legal-response-drafting.json).

## lifecycle-email-marketing

Plan lifecycle sequences, timing, triggers, exits and individual emails.

- Original: **emails**, by **Corey Haines / contributors; retain upstream copyright and notices.**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/emails/SKILL.md) · [discovery](https://www.skills.sh/coreyhaines31/marketingskills/emails).
- Licence: MIT; [full text](skills/lifecycle-email-marketing/LICENSE). Status: core.
- Experts: Maya, Remy.
- Evidence: skills.sh displayed installs (rounded where shown): 62.9K; GitHub repository stars, not individual skill users: 51391; Pinned repository last commit date (not per-skill): 2026-09-05T04:48:02Z; User reproduces broken support links in installed emails/churn-prevention copies; says v2 improved. Repository/package evidence, not endorsement of all skills.: Issue #524, installed copies dated 2026-08-16; unresolved portable-file issue
- [Source, usage evidence, requirements and recorded review](provenance/skills/lifecycle-email-marketing.json).

## market-size-estimation

Estimate TAM, SAM and SOM using sourced top-down and bottom-up methods, reconcile them, and expose growth assumptions and uncertainty.

- Original: **market-sizing**, by **Paweł Huryn**. [Pinned source](https://github.com/phuryn/pm-skills/blob/8607e3b077817f89bf4a9b623246219734ac3be0/pm-market-research/skills/market-sizing/SKILL.md) · [discovery](https://skills.sh/phuryn/pm-skills/market-sizing).
- Licence: MIT; [full text](skills/market-size-estimation/LICENSE). Status: core.
- Experts: Zara.
- Evidence: individual-installs: 2.7K all-time installs displayed; repo-stars: 26581; maintenance: Current pinned commit 8607e3b077817f89bf4a9b623246219734ac3be0 at 2026-09-14T21:15:01Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/market-size-estimation.json).

## marketing-content-strategy

Plan evidence-led topics, content clusters and distribution.

- Original: **content-strategy**, by **Corey Haines / contributors; retain upstream copyright and notices.**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/content-strategy/SKILL.md) · [discovery](https://www.skills.sh/coreyhaines31/marketingskills/content-strategy).
- Licence: MIT; [full text](skills/marketing-content-strategy/LICENSE). Status: core.
- Experts: Maria, Maya.
- Evidence: skills.sh displayed cumulative install telemetry, not active users: 144.6K; GitHub repository stars, not individual skill users: 51391; Pinned repository last commit date (not per-skill): 2026-09-05T04:48:02Z; User reproduces broken support links in installed emails/churn-prevention copies; says v2 improved. Repository/package evidence, not endorsement of all skills.: Issue #524, installed copies dated 2026-08-16; unresolved portable-file issue
- [Source, usage evidence, requirements and recorded review](provenance/skills/marketing-content-strategy.json).

## marketing-copy-editing

Polish drafts and refresh existing copy with voice and evidence checks.

- Original: **copy-editing**, by **Corey Haines / contributors; retain upstream copyright and notices.**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/copy-editing/SKILL.md) · [discovery](https://www.skills.sh/coreyhaines31/marketingskills/copy-editing).
- Licence: MIT; [full text](skills/marketing-copy-editing/LICENSE). Status: core.
- Experts: Jules, Maria, Noor, Remy.
- Evidence: skills.sh displayed installs (rounded where shown): 130.0K; GitHub repository stars, not individual skill users: 51391; Pinned repository last commit date (not per-skill): 2026-09-05T04:48:02Z; User reproduces broken support links in installed emails/churn-prevention copies; says v2 improved. Repository/package evidence, not endorsement of all skills.: Issue #524, installed copies dated 2026-08-16; unresolved portable-file issue
- [Source, usage evidence, requirements and recorded review](provenance/skills/marketing-copy-editing.json).

## marketing-copywriting

Create conversion-focused page copy, headlines and CTAs.

- Original: **copywriting**, by **Corey Haines / contributors; retain upstream copyright and notices.**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/copywriting/SKILL.md) · [discovery](https://www.skills.sh/coreyhaines31/marketingskills/copywriting).
- Licence: MIT; [full text](skills/marketing-copywriting/LICENSE). Status: core.
- Experts: Maria, Maya.
- Evidence: skills.sh displayed cumulative install telemetry, not active users: 207.0K; GitHub repository stars, not individual skill users: 51391; Pinned repository last commit date (not per-skill): 2026-09-05T04:48:02Z; User reproduces broken support links in installed emails/churn-prevention copies; says v2 improved. Repository/package evidence, not endorsement of all skills.: Issue #524, installed copies dated 2026-08-16; unresolved portable-file issue
- [Source, usage evidence, requirements and recorded review](provenance/skills/marketing-copywriting.json).

## month-end-close-management

Plan and coordinate month-end close tasks,dependencies,owners and review status.

- Original: **close-management**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/finance/skills/close-management/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/close-management).
- Licence: Apache-2.0; [full text](skills/month-end-close-management/LICENSE). Status: core.
- Experts: Daniel, Mina.
- Evidence: Installs (skills.sh displayed count; installations, not unique users): 2.8K; GitHub repository stargazers_count (repository-wide, not candidate-specific use): 25533; GitHub repository pushed_at (repository-wide, not proof this skill was recently edited): 2026-09-24T07:36:14Z; Weekly installs (8 displayed buckets, dates not exposed in label; same skills.sh telemetry source): 86, 73, 92, 63, 66, 51, 65, 80
- [Source, usage evidence, requirements and recorded review](provenance/skills/month-end-close-management.json).

## multi-source-research-synthesis

Turn investor/company document and discussion inputs into attributed briefings with conflicts and uncertainty visible.

- Original: **knowledge-synthesis**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/enterprise-search/skills/knowledge-synthesis/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/knowledge-synthesis).
- Licence: Apache-2.0; [full text](skills/multi-source-research-synthesis/LICENSE). Status: core.
- Experts: Frankie, Kai, Theo.
- Evidence: Installs (skills.sh displayed installations,not unique users): 6.1K; GitHub stargazers_count; repository-wide popularity,not individual skill use: 25533; Repository pushed_at; not per-skill latest edit: 2026-09-24T07:36:14Z; individual-installs: 6.1K
- [Source, usage evidence, requirements and recorded review](provenance/skills/multi-source-research-synthesis.json).

## nda-risk-review

Triage commercial NDAs against the team's attorney-reviewed positions and route exceptions to counsel.

- Original: **nda-review**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/claude-for-legal/blob/4a6c651889c97cc9140580363c73e0eb17379c2b/commercial-legal/skills/nda-review/SKILL.md) · [discovery](https://skills.sh/anthropics/claude-for-legal/nda-review).
- Licence: Apache-2.0; [full text](skills/nda-risk-review/LICENSE). Status: core.
- Experts: Ellis.
- Evidence: Installs (skills.sh visible label; not unique users): 643; GitHub stargazers_count (repository-wide, not individual-skill use): 9516; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-09-24T11:06:40Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/nda-risk-review.json).
- Evidence qualification: Lower-adoption specialist selection: 643 installs. Publisher/repository evidence and substantive source review support selection, but individual uptake is smaller and effectiveness is not independently proven.

## operational-risk-assessment

Build a prioritized operational risk register using likelihood, impact, mitigation, owner and status.

- Original: **risk-assessment**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/operations/skills/risk-assessment/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/risk-assessment).
- Licence: Apache-2.0; [full text](skills/operational-risk-assessment/LICENSE). Status: core.
- Experts: Frankie, James, Vera.
- Evidence: Installs (skills.sh displayed installations,not unique users): 3.1K; GitHub stargazers_count; repository-wide popularity,not individual skill use: 25533; Repository pushed_at; not per-skill latest edit: 2026-09-24T07:36:14Z; individual-installs: 3.1K
- [Source, usage evidence, requirements and recorded review](provenance/skills/operational-risk-assessment.json).

## operational-runbook-writing

Document an operational procedure with prerequisites, exact steps, expected results, failures, verification, rollback and escalation.

- Original: **runbook**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/operations/skills/runbook/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/runbook).
- Licence: Apache-2.0; [full text](skills/operational-runbook-writing/LICENSE). Status: core.
- Experts: James.
- Evidence: individual-installs: 2.9K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/operational-runbook-writing.json).

## partner-co-marketing

Find compatible audience-sharing partners, design mutual-value proposals, coordinate joint campaigns, and assess their leads, engagement and commercial contribution.

- Original: **co-marketing**, by **Corey Haines**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/co-marketing/SKILL.md) · [discovery](https://skills.sh/coreyhaines31/marketingskills/co-marketing).
- Licence: MIT; [full text](skills/partner-co-marketing/LICENSE). Status: core.
- Experts: Anika, Max.
- Evidence: individual-installs: 66.4K all-time installs displayed; repo-stars: 51420; maintenance: Current pinned repository commit 5b2c0007766c6a1cf1d53fd8fc73e979e0821022 dated 2026-09-05T04:48:02Z; maintenance: Latest primary-file commit 9cd82d3cdab5d251bae79c23d466a8f9e6ce9426 at 2026-08-23T21:23:42Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/partner-co-marketing.json).

## people-analytics-reporting

Produce workforce reports covering headcount, hiring, attrition, engagement, diversity and organizational trends.

- Original: **people-report**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/human-resources/skills/people-report/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/people-report).
- Licence: Apache-2.0; [full text](skills/people-analytics-reporting/LICENSE). Status: core.
- Experts: Ines.
- Evidence: individual-installs: 2.5K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/people-analytics-reporting.json).

## portfolio-company-performance-review

Review a portfolio company’s periodic financial package against budget and prior periods, flag material variances and summarize KPIs/covenants for management.

- Original: **portfolio-monitoring**, by **Anthropic FSI**. [Pinned source](https://github.com/anthropics/financial-services/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/vertical-plugins/private-equity/skills/portfolio-monitoring/SKILL.md) · [discovery](https://skills.sh/anthropics/financial-services/portfolio-monitoring).
- Licence: Apache-2.0; [full text](skills/portfolio-company-performance-review/LICENSE). Status: core.
- Experts: Daniel.
- Evidence: individual-installs: 968; repo-stars: 37338; maintenance: 2026-09-21T21:10:41Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/portfolio-company-performance-review.json).

## pricing-and-packaging-strategy

Evaluate value metrics, tier packaging, willingness-to-pay research and price-change rollout options for SaaS and related products.

- Original: **pricing**, by **Corey Haines**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/pricing/SKILL.md) · [discovery](https://skills.sh/coreyhaines31/marketingskills/pricing).
- Licence: MIT; [full text](skills/pricing-and-packaging-strategy/LICENSE). Status: core.
- Experts: Zara.
- Evidence: individual-installs: 64.7K all-time installs displayed; repo-stars: 51420; maintenance: Current pinned repository commit 5b2c0007766c6a1cf1d53fd8fc73e979e0821022 dated 2026-09-05T04:48:02Z; maintenance: Latest primary-file commit b6605e4ed2a776388910ea95bc486ef2eb68d133 at 2026-08-23T21:23:50Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/pricing-and-packaging-strategy.json).

## product-experiment-design

Design inexpensive behavioral experiments to test assumptions about an existing product before full implementation.

- Original: **brainstorm-experiments-existing**, by **Pawel Huryn**. [Pinned source](https://github.com/phuryn/pm-skills/blob/8607e3b077817f89bf4a9b623246219734ac3be0/pm-product-discovery/skills/brainstorm-experiments-existing/SKILL.md) · [discovery](https://www.skills.sh/phuryn/pm-skills/brainstorm-experiments-existing).
- Licence: MIT; [full text](skills/product-experiment-design/LICENSE). Status: core.
- Experts: Alex.
- Evidence: individual-installs: 2.6K installs displayed; repo-stars: 26581; maintenance: Latest repository commit observed: 8607e3b077817f89bf4a9b623246219734ac3be0 at 2026-09-14T21:15:01Z; Merge origin/main (v2.1.0) into the code-review skill branch; maintenance: Selected path latest change on or before pin: a372bee16dc2275e26078ca70a2eb7614ea316f7 at 2026-03-03T07:38:42Z; Improve skill discoverability
- [Source, usage evidence, requirements and recorded review](provenance/skills/product-experiment-design.json).

## product-launch-marketing

Plan phased product or feature launches across owned, rented and partner audiences, with readiness checks, coordinated assets and post-launch momentum.

- Original: **launch**, by **Corey Haines**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/launch/SKILL.md) · [discovery](https://skills.sh/coreyhaines31/marketingskills/launch).
- Licence: MIT; [full text](skills/product-launch-marketing/LICENSE). Status: core.
- Experts: Noor, Zara.
- Evidence: individual-installs: 63.0K all-time installs displayed; repo-stars: 51420; maintenance: Current pinned repository commit 5b2c0007766c6a1cf1d53fd8fc73e979e0821022 dated 2026-09-05T04:48:02Z; maintenance: Latest primary-file commit 8d877c663e9c8a4adafab595417f156ededf1b92 at 2026-08-23T21:30:33Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/product-launch-marketing.json).

## product-marketing-context

Establish shared audience, positioning and brand voice.

- Original: **product-marketing**, by **Corey Haines / contributors; retain upstream copyright and notices.**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/product-marketing/SKILL.md) · [discovery](https://www.skills.sh/coreyhaines31/marketingskills/product-marketing).
- Licence: MIT; [full text](skills/product-marketing-context/LICENSE). Status: core.
- Experts: Jules, Maria, Maya, Nadia, Remy, Zara.
- Evidence: skills.sh displayed installs (rounded where shown): 68.5K; GitHub repository stars, not individual skill users: 51391; Pinned repository last commit date (not per-skill): 2026-09-05T04:48:02Z; User reproduces broken support links in installed emails/churn-prevention copies; says v2 improved. Repository/package evidence, not endorsement of all skills.: Issue #524, installed copies dated 2026-08-16; unresolved portable-file issue
- [Source, usage evidence, requirements and recorded review](provenance/skills/product-marketing-context.json).

## product-metrics-dashboard-design

Specify product metrics and a monitoring dashboard with definitions, data sources, targets, alert thresholds and review ownership.

- Original: **metrics-dashboard**, by **Pawel Huryn**. [Pinned source](https://github.com/phuryn/pm-skills/blob/8607e3b077817f89bf4a9b623246219734ac3be0/pm-product-discovery/skills/metrics-dashboard/SKILL.md) · [discovery](https://www.skills.sh/phuryn/pm-skills/metrics-dashboard).
- Licence: MIT; [full text](skills/product-metrics-dashboard-design/LICENSE). Status: core.
- Experts: Alex.
- Evidence: individual-installs: 2.8K installs displayed; repo-stars: 26581; maintenance: Latest repository commit observed: 8607e3b077817f89bf4a9b623246219734ac3be0 at 2026-09-14T21:15:01Z; Merge origin/main (v2.1.0) into the code-review skill branch; maintenance: Selected path latest change on or before pin: a372bee16dc2275e26078ca70a2eb7614ea316f7 at 2026-03-03T07:38:42Z; Improve skill discoverability
- [Source, usage evidence, requirements and recorded review](provenance/skills/product-metrics-dashboard-design.json).

## product-requirements-writing

Draft a scoped product specification with problem, goals/non-goals, user stories, prioritized requirements, testable acceptance criteria, metrics and open questions.

- Original: **write-spec**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/product-management/skills/write-spec/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/write-spec).
- Licence: Apache-2.0; [full text](skills/product-requirements-writing/LICENSE). Status: core.
- Experts: Alex, Priya.
- Evidence: individual-installs: 3.3K installs displayed; repo-stars: 25556; maintenance: Latest repository commit observed: da38ec1ee89d41e5380e652a97382695003396e7 at 2026-09-24T19:33:00Z; adobe-for-creativity: display name "Adobe" (#1245); maintenance: Selected path latest change on or before pin: 2d6f7e22dd25593f0f748010430ef86f19659735 at 2026-03-13T15:57:57Z; Migrate commands to skills across all plugins
- [Source, usage evidence, requirements and recorded review](provenance/skills/product-requirements-writing.json).

## product-research-synthesis

Synthesize interviews, surveys, feedback and support tickets into evidenced themes, insights and product opportunities.

- Original: **synthesize-research**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/product-management/skills/synthesize-research/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/synthesize-research).
- Licence: Apache-2.0; [full text](skills/product-research-synthesis/LICENSE). Status: core.
- Experts: Alex, Priya, Robin, Sasha.
- Evidence: individual-installs: 2.9K installs displayed; repo-stars: 25556; maintenance: Latest repository commit observed: da38ec1ee89d41e5380e652a97382695003396e7 at 2026-09-24T19:33:00Z; adobe-for-creativity: display name "Adobe" (#1245); maintenance: Selected path latest change on or before pin: 2d6f7e22dd25593f0f748010430ef86f19659735 at 2026-03-13T15:57:57Z; Migrate commands to skills across all plugins
- [Source, usage evidence, requirements and recorded review](provenance/skills/product-research-synthesis.json).

## product-roadmap-planning

Create or update a roadmap, reprioritize work, show capacity/dependency trade-offs and explain what changed.

- Original: **roadmap-update**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/product-management/skills/roadmap-update/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/roadmap-update).
- Licence: Apache-2.0; [full text](skills/product-roadmap-planning/LICENSE). Status: core.
- Experts: Alex, Priya.
- Evidence: individual-installs: 2.9K installs displayed; repo-stars: 25556; maintenance: Latest repository commit observed: da38ec1ee89d41e5380e652a97382695003396e7 at 2026-09-24T19:33:00Z; adobe-for-creativity: display name "Adobe" (#1245); maintenance: Selected path latest change on or before pin: 2d6f7e22dd25593f0f748010430ef86f19659735 at 2026-03-13T15:57:57Z; Migrate commands to skills across all plugins
- [Source, usage evidence, requirements and recorded review](provenance/skills/product-roadmap-planning.json).

## product-stakeholder-update

Translate product progress into audience-specific executive, engineering, partner, customer or launch updates with risks, decisions and asks.

- Original: **stakeholder-update**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/product-management/skills/stakeholder-update/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/stakeholder-update).
- Licence: Apache-2.0; [full text](skills/product-stakeholder-update/LICENSE). Status: core.
- Experts: Alex, Priya.
- Evidence: individual-installs: 2.7K installs displayed; repo-stars: 25556; maintenance: Latest repository commit observed: da38ec1ee89d41e5380e652a97382695003396e7 at 2026-09-24T19:33:00Z; adobe-for-creativity: display name "Adobe" (#1245); maintenance: Selected path latest change on or before pin: 2d6f7e22dd25593f0f748010430ef86f19659735 at 2026-03-13T15:57:57Z; Migrate commands to skills across all plugins
- [Source, usage evidence, requirements and recorded review](provenance/skills/product-stakeholder-update.json).

## product-strategy-canvas

Create a product strategy canvas covering vision, customer problems, positioning, trade-offs, growth, capabilities, metrics and defensibility.

- Original: **product-strategy**, by **Pawel Huryn**. [Pinned source](https://github.com/phuryn/pm-skills/blob/8607e3b077817f89bf4a9b623246219734ac3be0/pm-product-strategy/skills/product-strategy/SKILL.md) · [discovery](https://www.skills.sh/phuryn/pm-skills/product-strategy).
- Licence: MIT; [full text](skills/product-strategy-canvas/LICENSE). Status: core.
- Experts: Alex.
- Evidence: individual-installs: 2.9K installs displayed; repo-stars: 26581; maintenance: Latest repository commit observed: 8607e3b077817f89bf4a9b623246219734ac3be0 at 2026-09-14T21:15:01Z; Merge origin/main (v2.1.0) into the code-review skill branch; maintenance: Selected path latest change on or before pin: a372bee16dc2275e26078ca70a2eb7614ea316f7 at 2026-03-03T07:38:42Z; Improve skill discoverability
- [Source, usage evidence, requirements and recorded review](provenance/skills/product-strategy-canvas.json).

## productivity-setup

Optional complete original productivity plugin for persistent tasks,memory,initialization and sync.

- Original: **start**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/productivity/skills/start/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/start).
- Licence: Apache-2.0; [full text](skills/productivity-setup/LICENSE). Status: conditional.
- Experts: Frankie, Kai.
- Evidence: Installs (skills.sh displayed installations,not unique users): 4.7K; GitHub stargazers_count; repository-wide popularity,not individual skill use: 25533; Repository pushed_at; not per-skill latest edit: 2026-09-24T07:36:14Z; individual-installs: 4.7K
- [Source, usage evidence, requirements and recorded review](provenance/skills/productivity-setup.json).

## productivity-task-sync

Optional complete original productivity plugin for persistent tasks,memory,initialization and sync.

- Original: **update**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/productivity/skills/update/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/update).
- Licence: Apache-2.0; [full text](skills/productivity-task-sync/LICENSE). Status: conditional.
- Experts: Frankie, Kai.
- Evidence: Installs (skills.sh displayed installations,not unique users): 4.8K; GitHub stargazers_count; repository-wide popularity,not individual skill use: 25533; Repository pushed_at; not per-skill latest edit: 2026-09-24T07:36:14Z; individual-installs: 4.8K
- [Source, usage evidence, requirements and recorded review](provenance/skills/productivity-task-sync.json).

## project-status-report

Assemble periodic leadership updates with KPIs, workstream progress, risks, decisions and next-period priorities.

- Original: **status-report**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/operations/skills/status-report/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/status-report).
- Licence: Apache-2.0; [full text](skills/project-status-report/LICENSE). Status: core.
- Experts: Frankie, James.
- Evidence: Installs (skills.sh displayed installations,not unique users): 2.8K; GitHub stargazers_count; repository-wide popularity,not individual skill use: 25533; Repository pushed_at; not per-skill latest edit: 2026-09-24T07:36:14Z; individual-installs: 2.8K
- [Source, usage evidence, requirements and recorded review](provenance/skills/project-status-report.json).

## recruiting-pipeline

Track candidates from sourcing to accepted offers and report stage velocity, conversions, source effectiveness and time to fill.

- Original: **recruiting-pipeline**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/human-resources/skills/recruiting-pipeline/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/recruiting-pipeline).
- Licence: Apache-2.0; [full text](skills/recruiting-pipeline/LICENSE). Status: core.
- Experts: Harper, Sofia.
- Evidence: Installs (skills.sh listing JSON-LD cumulative userInteractionCount; not unique users): 2769; GitHub stargazers_count (repository-wide, not individual-skill use): 25533; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-09-24T07:36:14Z; individual-installs: 2.8K
- [Source, usage evidence, requirements and recorded review](provenance/skills/recruiting-pipeline.json).

## sales-account-research

Research prospect accounts and contacts, check existing ownership, assess ICP fit and identify sourced outreach hooks.

- Original: **account-research**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/sales/skills/account-research/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/account-research).
- Licence: Apache-2.0; [full text](skills/sales-account-research/LICENSE). Status: core.
- Experts: Max.
- Evidence: Installs (skills.sh listing JSON-LD cumulative userInteractionCount; not unique users): 3159; GitHub stargazers_count (repository-wide, not individual-skill use): 25533; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/sales-account-research.json).

## sales-call-preparation

Prepare a cited meeting brief with account history, open commitments and discovery questions.

- Original: **call-prep**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/sales/skills/call-prep/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/call-prep).
- Licence: Apache-2.0; [full text](skills/sales-call-preparation/LICENSE). Status: core.
- Experts: Max.
- Evidence: Installs (skills.sh listing JSON-LD cumulative userInteractionCount; not unique users): 2812; GitHub stargazers_count (repository-wide, not individual-skill use): 25533; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/sales-call-preparation.json).

## sales-enablement-content

Create persona- and deal-stage-specific sales decks, one-pagers, objection responses, demos, proposals and playbooks that sellers or partners can use.

- Original: **sales-enablement**, by **Corey Haines**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/sales-enablement/SKILL.md) · [discovery](https://skills.sh/coreyhaines31/marketingskills/sales-enablement).
- Licence: MIT; [full text](skills/sales-enablement-content/LICENSE). Status: core.
- Experts: Anika, Max, Zara.
- Evidence: individual-installs: 105.4K all-time installs displayed; repo-stars: 51420; maintenance: Current pinned repository commit 5b2c0007766c6a1cf1d53fd8fc73e979e0821022 dated 2026-09-05T04:48:02Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/sales-enablement-content.json).

## sales-outreach-drafting

Draft personalized prospect emails and sequences, and carry out requested sends or enrollments through available connectors.

- Original: **draft-outreach**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/sales/skills/draft-outreach/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/draft-outreach).
- Licence: Apache-2.0; [full text](skills/sales-outreach-drafting/LICENSE). Status: core.
- Experts: Max.
- Evidence: Installs (skills.sh listing JSON-LD cumulative userInteractionCount; not unique users): 3086; GitHub stargazers_count (repository-wide, not individual-skill use): 25533; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/sales-outreach-drafting.json).

## sales-pipeline-review

Find stale, slipping and stuck deals, show pipeline coverage and prioritize follow-up.

- Original: **pipeline-review**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/sales/skills/pipeline-review/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/pipeline-review).
- Licence: Apache-2.0; [full text](skills/sales-pipeline-review/LICENSE). Status: core.
- Experts: Jordan, Max, Omar.
- Evidence: Installs (skills.sh visible label; not unique users): 2.6K; GitHub stargazers_count (repository-wide, not individual-skill use): 25533; GitHub pushed_at (repository-level activity, not proof of skill update): 2026-09-24T07:36:14Z; Latest commit touching exact SKILL.md at pinned revision: 2026-09-15T14:44:03Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/sales-pipeline-review.json).

## seo-report-generation

Run evidence-backed SEO audits and create the original saved HTML report.

- Original: **seo-report**, by **OpenSEO (plugin-declared author); root MIT copyright Ben Senescu, 2026.**. [Pinned source](https://github.com/every-app/open-seo/blob/0ffff93101043aad7600a3b6a499a0cd2887ef49/plugins/openseo/skills/seo-report/SKILL.md) · [discovery](https://www.skills.sh/every-app/open-seo/seo-report).
- Licence: MIT; [full text](skills/seo-report-generation/LICENSE). Status: conditional.
- Experts: Maria.
- Evidence: skills.sh displayed cumulative install telemetry, not active users: 368; Repository stars displayed by skills.sh, not individual users: 20.4K; Pinned commit directly rewrites SEO audit workflow; Git object metadata: 2026-09-19T16:55:56-07:00
- [Source, usage evidence, requirements and recorded review](provenance/skills/seo-report-generation.json).
- Evidence qualification: 368 installs; included only as the required original seo-audit dependency.

## social-media-management

Plan, repurpose and schedule platform-specific content and review engagement.

- Original: **social**, by **Corey Haines / contributors; retain upstream copyright and notices.**. [Pinned source](https://github.com/coreyhaines31/marketingskills/blob/5b2c0007766c6a1cf1d53fd8fc73e979e0821022/skills/social/SKILL.md) · [discovery](https://www.skills.sh/coreyhaines31/marketingskills/social).
- Licence: MIT; [full text](skills/social-media-management/LICENSE). Status: core.
- Experts: Jules.
- Evidence: skills.sh displayed installs (rounded where shown): 67.0K; GitHub repository stars, not individual skill users: 51391; Pinned repository last commit date (not per-skill): 2026-09-05T04:48:02Z; User reproduces broken support links in installed emails/churn-prevention copies; says v2 improved. Repository/package evidence, not endorsement of all skills.: Issue #524, installed copies dated 2026-08-16; unresolved portable-file issue
- [Source, usage evidence, requirements and recorded review](provenance/skills/social-media-management.json).

## software-debugging

Investigate a bug through reproducibility, evidence collection, a testable hypothesis, isolation and verification of the fix.

- Original: **debugging-strategies**, by **Seth Hobson**. [Pinned source](https://github.com/wshobson/agents/blob/4236bb91f8395b0435f1d8b8baf9e8e4c69a8620/plugins/developer-essentials/skills/debugging-strategies/SKILL.md) · [discovery](https://www.skills.sh/wshobson/agents/debugging-strategies).
- Licence: MIT; [full text](skills/software-debugging/LICENSE). Status: core.
- Experts: Casey, Robin.
- Evidence: individual-installs: 12.5K installs displayed; repo-stars: 39930; maintenance: Latest repository commit observed: 4236bb91f8395b0435f1d8b8baf9e8e4c69a8620 at 2026-09-13T14:43:53Z; ci: rebuild the Claude Code review workflow from scratch (#708); maintenance: Selected path latest change on or before pin: 47a5dbc3f9c2661c6afb13638f80d4a4d4449040 at 2026-03-07T15:53:17Z; fix(skills): remove phantom resource references and fix CoC links (#447)
- [Source, usage evidence, requirements and recorded review](provenance/skills/software-debugging.json).

## software-incident-response

Coordinate incident triage/status communication and produce a blameless postmortem with impact, timeline, causes and owned actions.

- Original: **incident-response**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/engineering/skills/incident-response/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/incident-response).
- Licence: Apache-2.0; [full text](skills/software-incident-response/LICENSE). Status: conditional.
- Experts: Casey.
- Evidence: individual-installs: 5.6K installs displayed; repo-stars: 25556; maintenance: Latest repository commit observed: da38ec1ee89d41e5380e652a97382695003396e7 at 2026-09-24T19:33:00Z; adobe-for-creativity: display name "Adobe" (#1245); maintenance: Selected path latest change on or before pin: 2d6f7e22dd25593f0f748010430ef86f19659735 at 2026-03-13T15:57:57Z; Migrate commands to skills across all plugins
- [Source, usage evidence, requirements and recorded review](provenance/skills/software-incident-response.json).

## software-test-planning

Choose test layers and cases for a change, prioritize critical/error/security/data paths, and identify coverage gaps.

- Original: **testing-strategy**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/engineering/skills/testing-strategy/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/testing-strategy).
- Licence: Apache-2.0; [full text](skills/software-test-planning/LICENSE). Status: core.
- Experts: Casey.
- Evidence: individual-installs: 6.1K installs displayed; repo-stars: 25556; maintenance: Latest repository commit observed: da38ec1ee89d41e5380e652a97382695003396e7 at 2026-09-24T19:33:00Z; adobe-for-creativity: display name "Adobe" (#1245); maintenance: Selected path latest change on or before pin: 4fa3cb92e2942d6594200fa8d2c800708e086072 at 2026-02-24T00:08:12Z; Big round of pushes
- [Source, usage evidence, requirements and recorded review](provenance/skills/software-test-planning.json).

## supply-chain-risk-auditor

Audit npm, PyPI and Go dependency metadata for version-matched advisories, abandoned upstreams, publisher concentration and install-script risk.

- Original: **supply-chain-risk-auditor**, by **Eric Quintero; published by Trail of Bits**. [Pinned source](https://github.com/trailofbits/skills/blob/32e34f8173796e3566a51aee877dc96bc5191f64/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md) · [discovery](https://www.skills.sh/trailofbits/skills/supply-chain-risk-auditor).
- Licence: CC-BY-SA-4.0; [full text](skills/supply-chain-risk-auditor/LICENSE). Status: core.
- Experts: Devon.
- Evidence: Installs (skills.sh displayed cumulative count, rounded where K is shown; not unique users): 7.0K; GitHub stargazers_count (repository-level, not skill usage): 7,226; Repository pushed_at (not individual skill revision): 2026-09-23T16:36:04Z; Most recent commit touching candidate directory (metadata changes may account for activity): 2026-09-16T22:05:09Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/supply-chain-risk-auditor.json).

## support-ticket-triage

Classify a support ticket, assess priority and impact, search for duplicates, route it, and prepare an initial response.

- Original: **ticket-triage**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/customer-support/skills/ticket-triage/SKILL.md) · [discovery](https://www.skills.sh/anthropics/knowledge-work-plugins/ticket-triage).
- Licence: Apache-2.0; [full text](skills/support-ticket-triage/LICENSE). Status: conditional.
- Experts: Robin, Sasha.
- Evidence: individual-installs: 2.8K installs displayed; repo-stars: 25556; maintenance: Latest repository commit observed: da38ec1ee89d41e5380e652a97382695003396e7 at 2026-09-24T19:33:00Z; adobe-for-creativity: display name "Adobe" (#1245); maintenance: Selected path latest change on or before pin: 2d6f7e22dd25593f0f748010430ef86f19659735 at 2026-03-13T15:57:57Z; Migrate commands to skills across all plugins
- [Source, usage evidence, requirements and recorded review](provenance/skills/support-ticket-triage.json).

## task-list-management

Optional complete original productivity plugin for persistent tasks,memory,initialization and sync.

- Original: **task-management**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/productivity/skills/task-management/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/task-management).
- Licence: Apache-2.0; [full text](skills/task-list-management/LICENSE). Status: conditional.
- Experts: Frankie, Kai.
- Evidence: Installs (skills.sh displayed installations,not unique users): 7.0K; GitHub stargazers_count; repository-wide popularity,not individual skill use: 25533; Repository pushed_at; not per-skill latest edit: 2026-09-24T07:36:14Z; individual-installs: 7.0K
- [Source, usage evidence, requirements and recorded review](provenance/skills/task-list-management.json).

## team-capacity-planning

Compare workload, skills and available people/time/budget, identify resource gaps and develop hiring, contracting or reprioritization scenarios.

- Original: **capacity-plan**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/operations/skills/capacity-plan/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/capacity-plan).
- Licence: Apache-2.0; [full text](skills/team-capacity-planning/LICENSE). Status: core.
- Experts: James.
- Evidence: individual-installs: 2.7K; repo-stars: 25533; maintenance: 2026-09-24T07:36:14Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/team-capacity-planning.json).

## user-cohort-analysis

Explore supplied customer cohorts through retention/adoption summaries, curves and heatmaps, then suggest research to explain patterns.

- Original: **cohort-analysis**, by **Pawel Huryn**. [Pinned source](https://github.com/phuryn/pm-skills/blob/8607e3b077817f89bf4a9b623246219734ac3be0/pm-data-analytics/skills/cohort-analysis/SKILL.md) · [discovery](https://www.skills.sh/phuryn/pm-skills/cohort-analysis).
- Licence: MIT; [full text](skills/user-cohort-analysis/LICENSE). Status: core.
- Experts: Quinn.
- Evidence: Installs (skills.sh displayed cumulative count, rounded where K is shown; not unique users): 2.6K; GitHub stargazers_count (repository-level, not skill usage): 26,575; Repository pushed_at (not individual skill revision): 2026-09-14T21:15:33Z; Most recent commit touching candidate directory (metadata changes may account for activity): 2026-03-03T07:38:42Z
- [Source, usage evidence, requirements and recorded review](provenance/skills/user-cohort-analysis.json).

## vendor-contract-status

Inventory supplier agreements,renewal deadlines and missing contractual coverage.

- Original: **vendor-check**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/legal/skills/vendor-check/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/vendor-check).
- Licence: Apache-2.0; [full text](skills/vendor-contract-status/LICENSE). Status: core.
- Experts: Lena, Vera.
- Evidence: Installs (skills.sh displayed count; installations, not unique users): 2.6K; GitHub repository stargazers_count (repository-wide, not candidate-specific use): 25533; GitHub repository pushed_at (repository-wide, not proof this skill was recently edited): 2026-09-24T07:36:14Z; Weekly installs (8 displayed buckets, dates not exposed in label; same skills.sh telemetry source): 84, 71, 76, 60, 61, 44, 55, 69
- [Source, usage evidence, requirements and recorded review](provenance/skills/vendor-contract-status.json).

## vendor-evaluation

Review a vendor’s performance, cost, contract/renewal terms and risk, then prepare a renewal or negotiation recommendation.

- Original: **vendor-review**, by **Anthropic**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/operations/skills/vendor-review/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/vendor-review).
- Licence: Apache-2.0; [full text](skills/vendor-evaluation/LICENSE). Status: core.
- Experts: James, Vera.
- Evidence: Installs (skills.sh displayed count; installations, not unique users): 2.6K; GitHub repository stargazers_count (repository-wide, not candidate-specific use): 25533; GitHub repository pushed_at (repository-wide, not proof this skill was recently edited): 2026-09-24T07:36:14Z; Weekly installs (8 displayed buckets, dates not exposed in label; same skills.sh telemetry source): 88, 69, 76, 57, 63, 51, 57, 72
- [Source, usage evidence, requirements and recorded review](provenance/skills/vendor-evaluation.json).

## verification-before-completion

Require fresh verification commands and inspected results before claiming that a change, test, build or requirement is complete.

- Original: **verification-before-completion**, by **Jesse Vincent**. [Pinned source](https://github.com/obra/superpowers/blob/5bf4e78011075bcfc0dc295f0724994cd123ee71/skills/verification-before-completion/SKILL.md) · [discovery](https://www.skills.sh/obra/superpowers/verification-before-completion).
- Licence: MIT; [full text](skills/verification-before-completion/LICENSE). Status: core.
- Experts: Casey.
- Evidence: individual-installs: 220.4K installs displayed; repo-stars: 291211; maintenance: Latest repository commit observed: 5bf4e78011075bcfc0dc295f0724994cd123ee71 at 2026-09-19T00:31:35Z; Release v6.4.1: diagnosing-superpowers, Native plan execution, OpenCode 2.0 and Muse support (#2338); maintenance: Selected path latest change on or before pin: 3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b at 2026-07-24T00:27:16Z; refactor(skills): drop persuasion sections from verification-before-completion
- [Source, usage evidence, requirements and recorded review](provenance/skills/verification-before-completion.json).

## website-seo-audit

Run evidence-backed SEO audits and create the original saved HTML report.

- Original: **seo-audit**, by **OpenSEO (plugin-declared author); root MIT copyright Ben Senescu, 2026.**. [Pinned source](https://github.com/every-app/open-seo/blob/0ffff93101043aad7600a3b6a499a0cd2887ef49/plugins/openseo/skills/seo-audit/SKILL.md) · [discovery](https://www.skills.sh/every-app/open-seo/seo-audit).
- Licence: MIT; [full text](skills/website-seo-audit/LICENSE). Status: conditional.
- Experts: Maria.
- Evidence: skills.sh displayed cumulative install telemetry, not active users: 3.5K; Repository stars displayed by skills.sh, not individual users: 20.4K; Pinned commit directly rewrites SEO audit workflow; Git object metadata: 2026-09-19T16:55:56-07:00
- [Source, usage evidence, requirements and recorded review](provenance/skills/website-seo-audit.json).

## workplace-memory-management

Optional complete original productivity plugin for persistent tasks,memory,initialization and sync.

- Original: **memory-management**, by **Anthropic and upstream contributors**. [Pinned source](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/productivity/skills/memory-management/SKILL.md) · [discovery](https://skills.sh/anthropics/knowledge-work-plugins/memory-management).
- Licence: Apache-2.0; [full text](skills/workplace-memory-management/LICENSE). Status: conditional.
- Experts: Frankie, Kai.
- Evidence: Installs (skills.sh displayed installations,not unique users): 7.2K; GitHub stargazers_count; repository-wide popularity,not individual skill use: 25533; Repository pushed_at; not per-skill latest edit: 2026-09-24T07:36:14Z; individual-installs: 7.2K
- [Source, usage evidence, requirements and recorded review](provenance/skills/workplace-memory-management.json).
