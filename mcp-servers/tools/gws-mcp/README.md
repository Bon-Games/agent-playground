# Google Workspace MCP

Local Dockerfile build from `tools/gws-mcp/Dockerfile`.

Provides Google Workspace tools (Drive, Calendar, Gmail) to Claude via MCP.

## Required environment variables

Add these to your `.env` file:

```
GOOGLE_CREDENTIALS_FILE=/path/to/your/service-account.json
```

The credentials file is mounted read-only into the container at `/app/credentials.json`.

## Getting a service account

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Create a service account and download the JSON key.
3. Enable the Google Workspace APIs you need (Drive, Calendar, Gmail, etc.).
4. Set `GOOGLE_CREDENTIALS_FILE` to the path of the downloaded JSON key.

## Note on package name

The `CMD` in the Dockerfile uses `@googleapis/mcp-server-workspace`. If this package is not yet published under that name, update the CMD to the correct npm package name.
