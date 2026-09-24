> Packaging adaptation by AutoGPT, 2026-09-25. Original authorship and licence are retained. Changes are limited to the recorded name, metadata and file references; see ATTRIBUTION.md in this skill package.

# Connectors

## How tool references work

Plugin files use `~~category` as a placeholder for whatever tool the user connects in that category. For example, `~~HRIS` might mean Workday, BambooHR, or any other HRIS with an MCP server.

Plugins are **tool-agnostic** — they describe workflows in terms of categories (HRIS, ATS, email, etc.) rather than specific products. The [upstream MCP configuration](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/human-resources/.mcp.json) pre-configures specific MCP servers, but any MCP server in that category works.

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
