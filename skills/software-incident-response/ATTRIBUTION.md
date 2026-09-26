# Attribution: software-incident-response

Original skill: `incident-response`.
Original author: Anthropic
Source: https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/engineering/skills/incident-response/SKILL.md
Pinned commit: `8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c`.
Licence: Apache-2.0; see LICENSE and any bundled notices.

AutoGPT curates and adapts packaging. The original author wrote the skill instructions. No expert advice or approval gate was rewritten. Original bytes and counted packaging edits are retained in provenance/files.json.

## Files and recorded changes

- `SKILL.md`: Relocate the explicitly referenced original connector documentation inside this self-contained package.; Previously approved clear package name and standard licence/source metadata; preserve all other authored fields and instructions.; Identify packaging modifications without claiming upstream authorship. Original: anthropics/knowledge-work-plugins/engineering/skills/incident-response/SKILL.md
- `LICENSE`: Copied unchanged. Original: anthropics/knowledge-work-plugins/LICENSE
- `references/CONNECTORS.md`: Make the original optional native plugin configuration an exact pinned setup-documentation link; this flat skill does not install or execute a plugin manifest.; Identify packaging modifications without claiming upstream authorship. Original: anthropics/knowledge-work-plugins/engineering/CONNECTORS.md

## Runtime requirements

- For Casey, use its authored postmortem mode with incident evidence and owner review.
- Full live-incident mode requires organization acceptance of native SEV1-4 response targets and properly authorized monitoring/incident/chat connectors.

## Remaining integration requirements

- Live incident modes require an organization-compatible original severity/response model, authorized monitoring/incident/chat connectors and responders. The original manual incident/postmortem drafting modes remain present. Packaging neither provisions those tools nor removes the live modes.

Not executed or benchmarked. Import acceptance does not establish runtime behavior.
