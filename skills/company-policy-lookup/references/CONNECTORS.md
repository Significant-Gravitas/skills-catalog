> Packaging adaptation by AutoGPT, 2026-09-25. Original authorship and licence are retained. Changes are limited to the recorded name, metadata and local references; see ATTRIBUTION.md in this package.

# Connectors

## How tool references work

Plugin files use `~~category` as a placeholder for whatever tool the user connects in that category. For example, `~~HRIS` might mean Workday, BambooHR, or any other HRIS with an MCP server.

Plugins are **tool-agnostic** — they describe workflows in terms of categories (HRIS, ATS, email, etc.) rather than specific products. The [upstream MCP configuration](https://github.com/anthropics/knowledge-work-plugins/blob/8f8779a1681ea2f8dc697a6b3063d5e3e7f7460c/human-resources/.mcp.json) pre-configures specific MCP servers, but any MCP server in that category works.

## Connectors for this plugin

| Category | Placeholder | Included servers | Other options |
|----------|-------------|-----------------|---------------|
| ATS | `~~ATS` | — | Greenhouse, Lever, Ashby, Workable |
| Calendar | `~~calendar` | Google Calendar | Microsoft 365 |
| Chat | `~~chat` | Slack | Microsoft Teams |
| Email | `~~email` | Gmail, Microsoft 365 | — |
| HRIS | `~~HRIS` | — | Workday, BambooHR, Rippling, Gusto |
| Knowledge base | `~~knowledge base` | Notion, Atlassian (Confluence) | Guru, Coda |
| Compensation data | `~~compensation data` | — | Pave, Radford, Levels.fyi |
