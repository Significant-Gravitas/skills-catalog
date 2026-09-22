# Provenance of the platform-authored expert skills

The skills bundled by the machine-built experts (Robin, Anika, Alex, Daniel, Sofia, Blake, Maya, James, Zara) were produced by the `muse-made-bots` build workflow: ten job-description researchers per role, a reuse hunt over the earlier packages, an adversarial review loop, and a web sweep for current practice. Each skill's build carried a reuse note naming what it adapted and from where. Those notes were dropped when the skills were converted to the platform format; this file keeps them. Where a skill was renamed in conversion, the note is listed under the catalog slug with the name it was built as.

## What this means for licensing

Two kinds of donor appear below. `muse-made-bots/...` and `grok-bots/...` are earlier packages from the same in-house pipeline. Everything else is an external source the builder read for frameworks, benchmarks, or practice — open-source skill repos and public articles.

On 2026-09-22 every in-repo skill (320 files) was scanned for shared 8-word sequences against all 27,845 markdown files in the external repos listed here. No skill shares 1% or more of its 8-grams with any donor, and no shared span reaches 12 words; the longest is nine, and those are stock formulas (the MEDDPICC letters, the "for [who], [product] is a [category] that [benefit]" positioning template). The external repos informed structure and framework names; their text was not copied, so no licence notice is owed. They are credited here anyway, and the entries in `catalog.yml` whose build notes cite an external repository carry an `adapted_from` list naming it with its licence. `adapted_from` means "shaped by" — the skill is platform-authored and its text is its own — which is why it is a separate field from `source`/`license`, the platform's slot for a vendored copy that is shown as attribution on the listing.

A second check on 2026-09-22 compared each such skill sentence-by-sentence (difflib on word sequences) against the specific donor file its note cites, which catches close paraphrase that an 8-gram scan cannot. The best matches for the framework donors score 0.17–0.42; the only pairs above 0.45 are stock formulas — the "for [who], [product] is a [category] that [benefit]" template and the MEDDPICC expansion — and no skill shares a heading with its donor.

## External repositories cited

| Repository | Licence |
|---|---|
| https://github.com/aviskaar/open-org | Apache-2.0 |
| https://github.com/classicchins/compounding-marketing | MIT |
| https://github.com/coreyhaines31/marketingskills | MIT |
| https://github.com/CraftOS-dev/craftbot-agent-bundles | MIT |
| https://github.com/csbailey5t/claude-skills-for-product-marketing | MIT |
| https://github.com/hah23255/pm-claude-skills | MIT |
| https://github.com/heynash/gtm-ai | MIT |
| https://github.com/LeadMagic/gtm-skills | MIT |
| https://github.com/MartinSPetkov/marketing-skills | MIT |
| https://github.com/menkesu/awesome-pm-skills | MIT |
| https://github.com/n2g7/agent-skills | MIT |
| https://github.com/obra/superpowers | MIT |
| https://github.com/robotijn/ctoc | PolyForm Shield 1.0.0 |
| https://github.com/sidoq530/B2B-revops-skills | MIT |
| https://github.com/standardbeagle/pm-skills | MIT |
| https://github.com/ZiDuNet/clawith-claude | Apache-2.0 |

Public articles and guides the web sweep cited are named inline in the notes below.

## Robin — built as `customer-service-rep-v4`

- **`account-health-and-qbrs`** — No reuse note recorded by the build.
- **`billing-refunds-and-exceptions`** — No reuse note recorded by the build.
- **`bpo-vendor-quality-ops`** — No reuse note recorded by the build.
- **`compliance-and-regulated-support`** — No reuse note recorded by the build.
- **`draft-the-reply`** — No reuse note recorded by the build.
- **`enterprise-identity-sso-support`** — No reuse note recorded by the build.
- **`escalations-and-incidents`** — No reuse note recorded by the build.
- **`fraud-and-chargeback-defense`** — No reuse note recorded by the build.
- **`robin-getting-started`** — No reuse note recorded by the build.
- **`help-center-answers-and-kb`** — No reuse note recorded by the build.
- **`knowledge-centered-service`** — No reuse note recorded by the build.
- **`live-channel-queue-operations`** — No reuse note recorded by the build.
- **`logistics-shipment-and-customs`** — No reuse note recorded by the build.
- **`marketplace-two-sided-mediation`** — No reuse note recorded by the build.
- **`mass-recovery-and-bulk-comms`** — No reuse note recorded by the build.
- **`member-benefits-and-claims`** — No reuse note recorded by the build.
- **`onboarding-and-adoption`** — No reuse note recorded by the build.
- **`orders-returns-and-warranty`** — No reuse note recorded by the build.
- **`own-to-closure`** — No reuse note recorded by the build.
- **`quality-csat-and-coaching`** — No reuse note recorded by the build.
- **`sensitive-data-safe-handling`** — No reuse note recorded by the build.
- **`service-recovery-and-goodwill`** — No reuse note recorded by the build.
- **`social-and-community-support`** — No reuse note recorded by the build.
- **`support-ops-improvement-program`** — No reuse note recorded by the build.
- **`technical-diagnostics-with-tools`** — No reuse note recorded by the build.
- **`travel-disruption-and-rebooking`** — No reuse note recorded by the build.
- **`triage-and-prioritize`** — No reuse note recorded by the build.
- **`troubleshoot-and-resolve`** — No reuse note recorded by the build.
- **`trust-and-safety-escalations`** — No reuse note recorded by the build.
- **`upsell-and-retention-offers`** — No reuse note recorded by the build.
- **`vip-and-white-glove-care`** — No reuse note recorded by the build.
- **`voice-and-phone-support`** — No reuse note recorded by the build.
- **`voice-of-customer-and-feedback`** — No reuse note recorded by the build.
- **`workforce-and-capacity-planning`** — No reuse note recorded by the build.

## Anika — built as `partner-manager-v4`

- **`assure-partner-led-delivery`** — No reuse note recorded by the build.
- **`build-data-and-r-d-alliances`** — No reuse note recorded by the build.
- **`build-partner-academies-at-scale`** — No reuse note recorded by the build.
- **`build-partner-led-category-creation`** — No reuse note recorded by the build.
- **`define-the-partner-icp`** — No reuse note recorded by the build.
- **`design-the-partner-program`** — No reuse note recorded by the build.
- **`drive-alliance-ma-and-strategic-investments`** — No reuse note recorded by the build.
- **`partner-first-touch-outreach`** (built as `first-touch-outreach`) — No reuse note recorded by the build.
- **`anika-getting-started`** — No reuse note recorded by the build.
- **`govern-the-strategic-alliance`** — No reuse note recorded by the build.
- **`handle-partner-conflict-and-churn`** (built as `handle-conflict-and-churn`) — No reuse note recorded by the build.
- **`manage-partner-renewals-and-exits`** (built as `manage-renewals-exits-change-control`) — No reuse note recorded by the build.
- **`map-the-partner-ecosystem`** (built as `map-the-ecosystem`) — No reuse note recorded by the build.
- **`model-the-partnership-commercials`** — No reuse note recorded by the build.
- **`onboard-and-enable-partners`** (built as `onboard-and-enable`) — No reuse note recorded by the build.
- **`orchestrate-multi-party-partner-bids`** (built as `orchestrate-multi-party-and-bid-motions`) — No reuse note recorded by the build.
- **`own-the-alliance-pnl`** — No reuse note recorded by the build.
- **`plan-the-multi-year-partnership`** — No reuse note recorded by the build.
- **`prep-the-partner-qbr`** — No reuse note recorded by the build.
- **`run-brand-oem-and-supply-partnerships`** (built as `run-brand-oem-supply-portfolios`) — No reuse note recorded by the build.
- **`run-creator-and-affiliate-partner-programs`** (built as `run-creator-and-affiliate-programs`) — No reuse note recorded by the build.
- **`run-global-partner-executive-councils`** — No reuse note recorded by the build.
- **`run-hyperscaler-marketplace-co-sell`** (built as `run-marketplace-co-sell`) — No reuse note recorded by the build.
- **`run-partner-strategy-and-operations`** — No reuse note recorded by the build.
- **`run-regulated-partnership-motions`** — No reuse note recorded by the build.
- **`run-the-partner-co-sell-cadence`** (built as `run-the-co-sell-cadence`) — No reuse note recorded by the build.
- **`run-the-partner-marketing-engine`** — No reuse note recorded by the build.
- **`scale-the-partner-channel`** (built as `scale-the-channel`) — No reuse note recorded by the build.
- **`scope-the-tech-partnership`** — No reuse note recorded by the build.
- **`set-board-level-alliance-strategy`** — No reuse note recorded by the build.
- **`source-and-qualify-partners`** — No reuse note recorded by the build.
- **`source-partners-via-investor-ecosystems`** (built as `source-via-startup-vc-pe-ecosystems`) — No reuse note recorded by the build.
- **`structure-the-partner-agreement`** (built as `structure-the-agreement`) — No reuse note recorded by the build.
- **`track-partner-pipeline`** — No reuse note recorded by the build.

## Alex — built as `product-manager`

- **`product-exec-briefing`** (built as `brief-the-room`) — Reuse: adoption/value/roadmap deck shape and every-number-sourced rule from grok-bots/ebr-value-deck-builder/skills/ebr-deck.md; KPI grade bands with forward commitments from muse-made-bots/joint-plan-builder/skills/qbr-prep.md; notes-only recap discipline from grok-bots/meeting-recap-deck/skills/build-the-recap-deck.md; exec narrative spine from financial-analyst board-and-investor-reporting.
- **`product-experiment-design`** (built as `design-the-experiment`) — Reuse: bottleneck-belief design with precommitted upgrade/ambiguous/downgrade bands from grok-bots/product-idea-stress-test/skills/pist-experiment-designer.md; control/variant/sample/SRM/CUPED output shape from robotijn/ctoc experiment-designer; ICE plus guardrail framing from zidunet/clawith-claude.
- **`alex-getting-started`** — Reuse: adapted from muse-made-bots/marketing-manager/skills/getting-started.md (connector check-first, prefs block, starter menu, routine offers, arc); PM questions and connectors swapped.
- **`product-market-and-competitor-read`** (built as `map-the-market`) — Reuse: what-changed/so-what/quiet shape with sourced links from grok-bots/competitor-watch/skills/weekly-competitor-brief.md; pricing-table extraction with no-estimate rule from pricing-and-packaging-comparison.md; watch-list setup from build-the-watch-list.md.
- **`product-roadmap-and-prioritization`** (built as `own-the-roadmap`) — Reuse: none — new skill. Corpus-wide grep found zero RICE/MoSCoW/Kano skills (raw-0 evidence); closest patterns (account-tiering weighted scoring, tune-the-decision-rubric backtest, score-and-qualify-leads tiers) score other domains and none covers backlog-to-roadmap with capacity check. Framework names follow awesome-pm-skills/prioritization-craft (MIT).
- **`product-launch-plan`** (built as `plan-the-launch`) — Reuse: tiered launch plan, messaging doc, go/no-go gate, and 90-day measure from muse-made-bots/marketing-manager/skills/plan-a-launch.md; enablement kit spec from muse-made-bots/partner-manager-v4/skills/onboard-and-enable.md; dated-milestone mechanics from sales-rep-v4 signature-to-launch-and-account-ops.
- **`product-metrics-and-instrumentation`** (built as `read-the-numbers`) — Reuse: movers-with-decomposition read and FACT/INFERENCE/UNKNOWN discipline from muse-made-bots/marketing-manager/skills/report-the-week.md; INPUT/OUTPUT metric definitions with R/Y/G and thin-sample rule from operations-manager build-the-ops-scorecard; metric-decomposition commentary from grok-bots/paid-media-report-desk/skills/what-moved-and-why.md.
- **`product-discovery-and-user-research`** (built as `run-discovery`) — Reuse: interview-prep flow from deanpeters discovery-interview-prep SKILL.md; verbatim-quote mining and repeated-language callout from grok-bots/customer-proof-desk/skills/mine-a-batch-of-calls.md; win-loss program shape and 3-account pattern bar from muse-made-bots/sales-rep-v4/skills/voice-of-customer-loop.md; ticket-batch theme mining from muse-made-bots/customer-service-rep-v2/skills/voice-of-customer-and-feedback.md.
- **`product-ai-feature-scoping-and-evals`** (built as `ship-the-ai-feature`) — Reuse: prompt-corpus design (count + mark-top-five pattern) from grok-bots/ai-search-visibility/skills/build-the-prompt-list.md, taxonomy adapted to feature-input kinds (happy-path/edge/adversarial/out-of-scope); capture-before-judge protocol from run-a-visibility-check.md; scoreboard with 3-run trend from share-of-answer-comparison.md; harness pointers promptfoo/deepeval/langfuse (OSS) from duty-0. New glue: nothing reused covers AI scoping-to-eval for PMs.
- **`product-prd-and-acceptance-criteria`** (built as `write-the-prd`) — Reuse: PRD section shape adapted from reqsmith-template and ancplua prd-template (Copy-as-Markdown pattern); MVP boundary and outcome slicing from grok-bots/tech-demos/skills/project-planning.md; one-ticket-per-finding shape from grok-bots/critiquito-design-critique/skills/hand-off-the-fixes.md (severity field adapted to story priority); wireframe-level states from grok-bots/figma-bro/skills/build-a-screen-from-a-brief.md.
- **`product-strategy-and-bets`** (built as `write-the-strategy`) — Reuse: narrative from grok-bots/ebr-value-deck-builder/skills/three-whys.md; for-and-against graded packets from grok-bots/product-idea-stress-test/skills/pist-evidence-investigator.md; strategy-doc shape informed by awesome-pm-skills/strategy-frameworks (MIT). New glue: nothing reused covers the PM strategy-doc-to-roadmap handoff.

## Daniel — built as `financial-analyst`

- **`automate-finance-reporting`** — No reuse note recorded by the build.
- **`finance-board-and-investor-reporting`** (built as `board-and-investor-reporting`) — No reuse note recorded by the build.
- **`budget-vs-actuals-and-reforecast`** (built as `budget-forecast-and-plan`) — No reuse note recorded by the build.
- **`cash-treasury-and-fx`** — No reuse note recorded by the build.
- **`close-controls-and-accounting`** — No reuse note recorded by the build.
- **`deal-economics-and-pricing-guardrails`** (built as `deal-desk-and-pricing`) — No reuse note recorded by the build.
- **`daniel-getting-started`** — No reuse note recorded by the build.
- **`saas-gtm-finance`** — No reuse note recorded by the build.
- **`unit-economics-and-roi`** — No reuse note recorded by the build.
- **`variance-and-flux-analysis`** — No reuse note recorded by the build.

## Sofia — built as `recruiter`

- **`hiring-debrief-and-decision`** (built as `debrief-and-decision-support`) — No reuse note recorded by the build.
- **`sofia-getting-started`** — No reuse note recorded by the build.
- **`role-intake-and-scorecard`** (built as `intake-and-role-scoping`) — No reuse note recorded by the build.
- **`interview-coordination`** — No reuse note recorded by the build.
- **`interview-kit-design`** — No reuse note recorded by the build.
- **`job-description-drafting`** — No reuse note recorded by the build.
- **`job-offer-and-close-plan`** (built as `offer-strategy-and-close`) — No reuse note recorded by the build.
- **`passive-candidate-outreach`** — No reuse note recorded by the build.
- **`hiring-pipeline-analytics`** (built as `pipeline-analytics`) — No reuse note recorded by the build.
- **`resume-screening`** — No reuse note recorded by the build.
- **`candidate-sourcing-strategy`** (built as `sourcing-strategy`) — No reuse note recorded by the build.

## Blake — built as `sales-rep-v4`

- **`alliance-co-commercialization`** — No reuse note recorded by the build.
- **`build-the-target-list`** — No reuse note recorded by the build.
- **`business-case-and-roi-selling`** — No reuse note recorded by the build.
- **`cloud-commit-and-marketplace-selling`** — No reuse note recorded by the build.
- **`compliance-gated-deal-execution`** — No reuse note recorded by the build.
- **`credit-term-sheet-structuring`** — No reuse note recorded by the build.
- **`discovery-and-qualification`** — No reuse note recorded by the build.
- **`draft-a-first-touch`** — No reuse note recorded by the build.
- **`draft-a-follow-up`** — No reuse note recorded by the build.
- **`enablement-playbooks-certification`** — No reuse note recorded by the build.
- **`enterprise-deal-desk-close-plans`** — No reuse note recorded by the build.
- **`exec-engagement-and-sponsorship`** — No reuse note recorded by the build.
- **`field-call-route-discipline`** — No reuse note recorded by the build.
- **`find-the-decision-makers`** — No reuse note recorded by the build.
- **`max-getting-started`** (shipped for a day as `blake-getting-started`) — No reuse note recorded by the build.
- **`handle-a-reply`** — No reuse note recorded by the build.
- **`industrial-pursuit-tender-handover`** — No reuse note recorded by the build.
- **`marketplace-partner-revenue-growth`** — No reuse note recorded by the build.
- **`media-plan-measure-optimize`** — No reuse note recorded by the build.
- **`multithread-and-stakeholder-maps`** — No reuse note recorded by the build.
- **`next-step-and-handoff`** — No reuse note recorded by the build.
- **`objection-and-negotiation`** — No reuse note recorded by the build.
- **`partner-and-channel-co-sell`** — No reuse note recorded by the build.
- **`pipeline-review-and-forecast`** — No reuse note recorded by the build.
- **`quarterback-the-deal-team`** — No reuse note recorded by the build.
- **`regional-category-gtm-strategy`** — No reuse note recorded by the build.
- **`regulated-access-and-clinical-selling`** — No reuse note recorded by the build.
- **`renewal-expansion-and-qbr`** — No reuse note recorded by the build.
- **`research-an-account`** — No reuse note recorded by the build.
- **`retail-jbp-trade-and-sellout`** — No reuse note recorded by the build.
- **`rfp-and-competitive-bid-response`** — No reuse note recorded by the build.
- **`sales-ops-coverage-and-quota`** — No reuse note recorded by the build.
- **`sales-team-leadership`** — No reuse note recorded by the build.
- **`showroom-fi-and-internet-bdc`** — No reuse note recorded by the build.
- **`signature-to-launch-and-account-ops`** — No reuse note recorded by the build.
- **`territory-and-account-planning`** — No reuse note recorded by the build.
- **`voice-of-customer-loop`** — No reuse note recorded by the build.

## Maya — built as `marketing-manager`

- `brief-and-recap-an-event` — not shipped. Build note: No reuse note recorded by the build.
- **`nurture-sequence-build-and-readout`** (built as `build-a-nurture`) — No reuse note recorded by the build.
- **`messaging-and-tone-matrix`** (built as `build-the-voice-profile`) — No reuse note recorded by the build.
- **`channel-draft-shapes`** (built as `draft-for-a-channel`) — No reuse note recorded by the build.
- **`maya-getting-started`** — No reuse note recorded by the build.
- **`campaign-brief-and-asset-plan`** (built as `plan-a-campaign`) — No reuse note recorded by the build.
- `plan-a-launch` — not shipped — Alex's product-launch-plan covers the launch plan. Build note: No reuse note recorded by the build.
- **`weekly-marketing-read`** (built as `report-the-week`) — No reuse note recorded by the build.
- **`editorial-calendar-ops`** (built as `run-the-editorial-calendar`) — No reuse note recorded by the build.
- **`content-brief-writer-handoff`** (built as `write-a-content-brief`) — No reuse note recorded by the build.

## James — built as `operations-manager`

- **`ops-automate-a-workflow`** (built as `automate-a-workflow`) — No reuse note recorded by the build.
- **`ops-scorecard-and-kpis`** (built as `build-the-ops-scorecard`) — No reuse note recorded by the build.
- **`james-getting-started`** — No reuse note recorded by the build.
- **`ops-govern-a-program`** (built as `govern-a-program`) — No reuse note recorded by the build.
- **`ops-map-and-improve-a-process`** (built as `map-and-improve-a-process`) — No reuse note recorded by the build.
- **`ops-capacity-and-headcount-plan`** (built as `plan-capacity-and-headcount`) — No reuse note recorded by the build.
- **`ops-controls-and-escalations`** (built as `run-controls-and-escalations`) — No reuse note recorded by the build.
- **`ops-run-the-operating-rhythm`** (built as `run-the-operating-rhythm`) — No reuse note recorded by the build.
- **`ops-vendor-and-procurement`** (built as `run-vendor-and-procurement-ops`) — No reuse note recorded by the build.
- **`ops-write-an-sop`** (built as `write-an-sop`) — No reuse note recorded by the build.

## Zara — built as `gtm-strategist`

- **`commercial-launch-strategy`** — Reuse: tiered launch plan (quiet/standard/tentpole), messaging doc, go/no-go gate, and 90-day measure from muse-made-bots/marketing-manager/skills/plan-a-launch.md; extended gate items (support, legal, pricing, feedback channel) plus retrospective from muse-made-bots/product-manager/skills/plan-the-launch.md; dated milestones with entry/exit criteria from muse-made-bots/sales-rep-v3/skills/signature-to-launch-and-account-ops.md. Hardened with 24h go/no-go + evidence-per-item patterns (hah23255/pm-claude-skills, oghma launch-checklist, verified via curl).
- **`competitive-intelligence`** — Reuse: what-changed/so-what/quiet shape with sourced links from grok-bots/competitor-watch/skills/weekly-competitor-brief.md; 4-page watch-list setup from build-the-watch-list.md; material-vs-noise diff bar from competitor-page-diff.md; 3-discriminator win strategy from muse-made-bots/sales-rep-v2/skills/rfp-and-competitive-bid-response.md; quoted-not-paraphrased win-loss loop from muse-made-bots/sales-rep-v4/skills/voice-of-customer-loop.md. Web audit: win/loss zones, Know/Say/Show, scenario variants, refresh-on-signal + provenance footer, 90-day deal-intel pane, review/demo/community sources.
- **`developer-and-api-motion`** — Reuse: North Star + input-metrics framing and instrumentation-before-read from muse-made-bots/product-manager/skills/read-the-numbers.md; developer-narrative and reference-architecture patterns from the AWS Serverless GTM data (jd-0). New: dev-funnel staging with time-to-first-call as the golden metric plus community/champion design, which no donor covers.
- **`field-enablement-content`** — Reuse: dated-play library with owners, cert gates, quality rubric, and quarterly refresh from muse-made-bots/sales-rep-v4/skills/enablement-playbooks-certification.md; 4-slide Why deck with sourced speaker notes from grok-bots/ebr-value-deck-builder/skills/three-whys.md; one-page proof sheet per prospect from grok-bots/customer-proof-desk/skills/build-a-deal-proof-one-pager.md; sub-30s talk-track writer from grok-bots/sales-call-coach/skills/objection-replay.md.
- **`zara-getting-started`** — Reuse: onboarding shape (first-output rule, skippable prefs, connector check-first, starter menu, routine offers, 30/60/90 arc) adapted from muse-made-bots/marketing-manager/skills/getting-started.md; GTM prefs and connectors are new for this bot.
- **`gtm-performance-diagnostics`** — Reuse: KPI scorecard builder with INPUT/OUTPUT types, R/Y/G, mover decomposition, and thin-sample rule from muse-made-bots/operations-manager/skills/build-the-ops-scorecard.md; coverage math, forecast grades, and hygiene flags from muse-made-bots/sales-rep/skills/pipeline-review-and-forecast.md; North Star + input-metrics framing from muse-made-bots/product-manager/skills/read-the-numbers.md; metric-decomposition commentary from grok-bots/paid-media-report-desk/skills/what-moved-and-why.md.
- **`gtm-planning-and-market-entry`** — Reuse: coverage design with tiered books, capacity model, and quota allocation from muse-made-bots/sales-rep-v4/skills/sales-ops-coverage-and-quota.md; readiness-gate items from muse-made-bots/product-manager/skills/plan-the-launch.md; operating-cadence shape from muse-made-bots/operations-manager/skills/run-the-operating-rhythm.md. New: per-segment motion design with entry/exit-sequenced market entry, which no donor covers.
- **`icp-and-segmentation`** — Reuse: 5-block ICP + strategic/growth/watch tiers with graduation and kill bars adapted from muse-made-bots/partner-manager/skills/define-the-partner-icp.md; tiered account-list mechanics from grok-bots/signal-prospector/skills/account-tiering.md and grok-bots/account-research-desk/skills/build-the-account-list.md. New: buyer-side ICP with anti-signals and deprioritization verdicts, which no donor covers. Web audit: trigger event + technographics, best-customer build rule, fit-vs-ready intent/budget layers, quarterly refresh, Best/Good/Bad rubric.
- **`opportunity-sizing-and-business-case`** — Reuse: driver-first forecasting with run-rate math and Base/Adverse/Opportunity grades from muse-made-bots/financial-analyst/skills/budget-forecast-and-plan.md; NRR/GRR, coverage, and efficiency reads from saas-gtm-finance.md; ROI and payback framing from muse-made-bots/sales-rep-v2/skills/business-case-and-roi-selling.md. New: TAM/SAM/SOM triangulation with method-disagreement ranges, which no donor covers (gap confirmed in reuse sweep). Web audit: 3x cross-check flag, 1–5% SOM capture guardrail.
- **`positioning-and-messaging`** — Reuse: one-line positioning + 3 proof points + never-claims + per-persona variants adapted from muse-made-bots/marketing-manager/skills/build-the-voice-profile.md; three-whys narrative from grok-bots/ebr-value-deck-builder/skills/three-whys.md; substitutes-including-doing-nothing from muse-made-bots/product-manager/skills/write-the-strategy.md. Frameworks informed by leadmagic/gtm-skills positioning-messaging (SKILL.md verified via curl). Web audit: Dunford 5-component spine + best-fit-only rule + persona x buying-stage matrix.
- **`pricing-and-packaging`** — Reuse: per-plan extraction tables with fetch dates and no-estimate rule from grok-bots/competitor-watch/skills/pricing-and-packaging-comparison.md; guardrail bands, deal P&L, and concession routing from muse-made-bots/financial-analyst/skills/deal-desk-and-pricing.md; mix-impact framing from unit-economics-and-roi.md. New: value-metric and tier-shape design plus grandfathering and rollout notes, which no donor covers. Web audit: Van Westendorp + forced-choice/Gabor-Granger/conjoint WTP methods, quarterly review, tiered discount SLAs with give-gets.
- **`sales-marketing-alignment-and-sla`** — New: no explicit sales-marketing SLA skill exists in the corpus (gap confirmed in reuse sweep); composed from lead-tier mechanics (grok-bots/lead-pipeline-desk/skills/score-and-qualify-leads.md), qualification bars (grok-bots/deal-inspector/skills/qualification-frameworks.md), sourced/influenced pipeline split (muse-made-bots/partner-manager/skills/track-partner-pipeline.md), and joint-scorecard shape (muse-made-bots/operations-manager/skills/build-the-ops-scorecard.md). Informed by leadmagic sales-marketing-sla SKILL and the Arise GTM SLA guide (verified via curl). Web audit: SAL stage, stage/status split, 100-pt starter scoring, numeric SLA defaults + escalation, caveated benchmark bars.
- **`vertical-industry-plays`** — Reuse: dated-play skeleton (trigger, ICP, value, motion, owners, targets, exit) from muse-made-bots/cosell-orchestrator/skills/design-the-co-sell-play.md; incumbent table with confirmed/likely/unknown grades from grok-bots/account-research-desk/skills/incumbent-and-competitor-check.md; ecosystem whitespace from muse-made-bots/partner-manager-v2/skills/map-the-ecosystem.md. New: industry-narrative plus compliance/proof-gated entry sequencing, which no donor covers.
