# Atlassian MCP

Docker Hub image: `mcp/atlassian:latest`

Provides Jira and Confluence tools to Claude via MCP.

## Required environment variables

Add these to your `.env` file:

```
CONFLUENCE_URL=https://your-org.atlassian.net/wiki
CONFLUENCE_USERNAME=your@email.com
CONFLUENCE_API_TOKEN=your_confluence_api_token
JIRA_URL=https://your-org.atlassian.net
JIRA_USERNAME=your@email.com
JIRA_API_TOKEN=your_jira_api_token
```

Generate API tokens at: https://id.atlassian.com/manage-profile/security/api-tokens

## Source

https://hub.docker.com/r/mcp/atlassian
