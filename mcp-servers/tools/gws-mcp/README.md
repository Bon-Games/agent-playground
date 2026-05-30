# Google Workspace MCP — Login Guide

An MCP server that gives Claude access to Gmail / Google Drive (and other
Workspace apps), running in Docker. Authentication uses **Google OAuth** — no
`gcloud` and no Google Cloud project required.

> You only log in **once**. The token is stored in the `ws-token` volume and
> refreshes automatically, so later sessions don't need to log in again.

## Requirements

- The `gws-mcp` image has been built (`docker compose build`).
- A device with a browser (computer or phone) to open the sign-in link.

## Log in (one time)

Run in a terminal:

```bash
docker compose run --rm gws-mcp node workspace-server/dist/index.js login
```

Follow the on-screen steps:

1. The command prints an **OAuth URL**.
2. Open that URL in any browser and sign in to your Google account.
3. The browser shows a **credentials JSON** blob. Copy all of it.
4. Paste the JSON back into the terminal and press Enter.
5. You're done when you see `Credentials saved successfully!`.

Credentials are read directly from the terminal (`/dev/tty`). They never pass
through Claude and are never exposed to the model.

## Check status

```bash
docker compose run --rm gws-mcp node scripts/auth-utils.js status
```

## Use it in Claude

Once logged in, just start Claude and use it normally. Type `/mcp` to see the
list — `gws` will appear as connected. Authentication happens transparently when
a Gmail / Drive tool is called.

## Re-authenticating

If the token is revoked or expires, Claude will return an error asking you to log
in when a tool is called. To fix it:

1. Open another terminal and run the login command above (it writes to the same
   volume).
2. Go back to Claude and **retry** the tool — the server picks up the new token
   automatically.

> **Important:** always use the same `hostname` (preset to `wsmcp` in
> `docker-compose.yml`) and the same `ws-token` volume. The token's encryption
> key is tied to the hostname; changing it makes the stored token undecryptable.

## Clear login

```bash
docker compose run --rm gws-mcp node scripts/auth-utils.js clear
```
