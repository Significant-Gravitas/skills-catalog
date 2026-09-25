> Packaging adaptation by AutoGPT, 2026-09-25. Original authorship and licence are retained. Changes are limited to the recorded name, metadata and local references; see ATTRIBUTION.md in this package.

# Connectors

## How tool references work

Plugin files use `~~category` as a placeholder for whatever tool the user connects in that category. For example, `~~support platform` might mean Intercom, Zendesk, or any other support tool with an MCP server.

Plugins are **tool-agnostic** — they describe workflows in terms of categories (support platform, CRM, chat, etc.) rather than specific products. The [upstream MCP configuration](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/customer-support/.mcp.json) pre-configures specific MCP servers, but any MCP server in that category works.

## Connectors for this plugin

| Category | Placeholder | Included servers | Other options |
|----------|-------------|-----------------|---------------|
| Chat | `~~chat` | Slack | Microsoft Teams |
| Email | `~~email` | Microsoft 365 | — |
| Cloud storage | `~~cloud storage` | Microsoft 365 | — |
| Support platform | `~~support platform` | Intercom | Zendesk, Freshdesk, HubSpot Service Hub |
| CRM | `~~CRM` | HubSpot | Salesforce, Pipedrive |
| Knowledge base | `~~knowledge base` | Guru, Notion | Confluence, Help Scout |
| Project tracker | `~~project tracker` | Atlassian (Jira/Confluence) | Linear, Asana |
