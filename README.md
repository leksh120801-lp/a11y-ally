# A11y Ally

A Slack agent that reviews a message, thread, or canvas for accessibility problems — poor
readability, jargon/unexplained acronyms, images missing alt text — and suggests a
plain-language rewrite. It never edits or posts anything on its own; every rewrite is
offered as a one-click suggestion that a human explicitly approves.

Built for the Slack **"Agent for Good" hackathon — accessibility track**.
Required hackathon technology: **MCP server integration**.

## What it does

1. Open A11y Ally from the **Agents** section of the Slack sidebar (or `@mention` it in a
   channel it's been invited to).
2. Ask it to review something — "Make this plain-language: ...", "Check this thread for
   accessibility issues", "Does this image have alt text?"
3. It analyzes the content using its own accessibility tools, shows its work as visible
   task-card steps, states the impact in plain terms (e.g. "reading grade 14 — aim for 8
   or below"), and — if it has a rewrite to suggest — shows **Copy rewrite** / **Post
   rewrite** buttons. Nothing is posted or changed until a human clicks one.

## Architecture: MCP host / client / server

```
┌─────────────────────────┐        ┌──────────────────────────┐        ┌───────────────────────────┐
│   Slack side panel       │        │   agent/ (Bolt app)       │        │   a11y-mcp/ (MCP server)   │
│   HOST                   │◄──────►│   CLIENT                  │◄──────►│   SERVER                   │
│                           │        │                            │        │                             │
│  - renders the chat UI   │  Bolt  │  - Gemini (Vertex AI) does │  MCP   │  - readability_score(text)  │
│  - streams task cards    │  API   │    the reasoning           │ stdio  │  - find_jargon(text)        │
│  - Copy/Post buttons     │        │  - starts a11y-mcp over    │        │  - alt_text_check(blocks)   │
│    (human-in-the-loop)   │        │    stdio, lists its tools, │        │                             │
│                           │        │    calls them on request   │        │  Pure functions, no Slack   │
└─────────────────────────┘        └──────────────────────────┘        └───────────────────────────┘
```

**Agent loop:** receive input → reason (Gemini) → call MCP tool(s) → stream output →
repeat until a final answer, then present it with human-in-the-loop actions.

- **Host** — Slack itself, specifically the Agents & AI Apps side panel. Renders the
  conversation, the streaming task-card UI, and the Block Kit buttons.
- **Client** — the Bolt agent in `agent/`. Owns the conversation loop: it calls the LLM,
  and whenever the LLM wants to use a tool, the client is the one that actually opens an
  MCP session to `a11y-mcp` and executes it (`agent/listeners/assistant/mcp_client.py`).
- **Server** — `a11y-mcp/`, a small `FastMCP` server that exposes three accessibility
  tools over stdio. It has no idea Slack exists; it just takes text/blocks in and returns
  structured accessibility findings out.

## Stack

- Python 3.10+
- [Bolt for Python](https://slack.dev/bolt-python/) (`agent/`), from the official
  `slack-samples/bolt-python-assistant-template`
- **Gemini (`gemini-2.5-flash`) via Vertex AI** as the reasoning LLM, authenticated with
  `gcloud` Application Default Credentials (no API key committed or required)
- A custom MCP server (`a11y-mcp/`) built with the official Python MCP SDK (`mcp[cli]`)
  and [`textstat`](https://pypi.org/project/textstat/) for readability scoring
- Socket Mode for local dev/demo — no public URL or ngrok tunnel required

> Note: the original design called for Claude as the reasoning model (see the "Agent
> loop" framing above). We built Phase 5 against Claude first, then switched to Gemini on
> Vertex AI once we hit Anthropic billing limits and had free GCP credits available
> instead. The MCP host/client/server architecture — the actual required hackathon
> technology — is unaffected by which LLM sits in the "reason" step.

## Setup

### 1. Slack app

Create a Slack app from `agent/manifest.json` at <https://api.slack.com/apps> → **Create
New App → From an app manifest**. Enable Socket Mode and generate an app-level token
(`connections:write` scope), then install the app to your workspace to get a bot token.

### 2. Agent (`agent/`)

```
cd agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `agent/.env`:

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

Authenticate with GCP (no API key needed):

```
gcloud auth login
gcloud config set project your-gcp-project-id
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com --project=your-gcp-project-id
```

### 3. MCP server (`a11y-mcp/`)

```
cd a11y-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The agent launches this server itself (as a subprocess, over stdio) — you don't need to
run it separately. To poke at the tools directly, use the MCP Inspector:

```
mcp dev server.py
```

### 4. Run

```
cd agent
source .venv/bin/activate
python app.py
```

Look for `⚡️ Bolt app is running!`, then open A11y Ally under **Agents** in Slack's
sidebar.

## Data hygiene

A11y Ally does not persist any Slack content. It pulls message/thread/canvas text and
block data live, at the moment of a request, analyzes it in memory, and discards it once
the turn ends — nothing is written to disk or a database. If we ever add memory across
turns, it would store only non-content metadata (e.g. a message's grade level, not the
message itself).

## Prompt-injection note

Channel content the agent reviews (message text, thread replies, canvas content) is
**data to analyze, not instructions to follow** — this is stated explicitly in the
system prompt. The agent never posts, edits, DMs, or exfiltrates anything based on
content it merely observed; every write action (currently: posting a rewrite) requires
an explicit human click on a Block Kit button, and even then only posts back into the
same thread the human is already in.

## Known limitations

- No `message.channels` scope/event — the agent only responds when @mentioned in a
  channel or when talked to directly in its side panel. It does not passively read every
  channel message.
- `find_jargon` and the alt-text check are heuristic (regex/allowlist-based), not ML
  models — good enough for a hackathon demo, not a production accessibility auditor.
- Vertex AI model availability is project/region-specific; `gemini-2.5-flash` is what
  worked on our test project — you may need to adjust `MODEL` in
  `agent/listeners/assistant/mcp_client.py` for yours.
