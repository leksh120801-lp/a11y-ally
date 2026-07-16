# Cleary: Technical Documentation

This document explains what Cleary is and how it works, twice over: once in plain
language, and once at the level of actual code and protocol details. Read the plain
language parts if you just want to understand the system; read the technical parts if
you're extending it, debugging it, or judging it as an MCP implementation.

---

## 1. What Cleary is (plain language)

Cleary is a little assistant that lives inside Slack. You can open it in a side panel,
same as you'd open any chat app, and ask it to look at a message, a conversation, or a
Slack canvas. It checks four things:

- Is this hard to read? (long sentences, big words, high "school grade level" needed)
- Does it use jargon or acronyms nobody explained?
- Are there pictures with no description for people using screen readers?
- Is it a wall of shouting, unstructured text that's exhausting to get through,
  especially for someone with dyslexia or ADHD?

If it finds a problem, it explains *why* it matters in plain terms (like, "this needs a
college graduate level to understand, aim for 8th grade") and offers a rewrite. Crucially,
it never sends that rewrite anywhere by itself. It shows you two buttons, "Copy rewrite"
and "Post rewrite," and only acts if you click one.

## 1a. What Cleary is (technical)

Cleary is a Slack app built with [Bolt for Python](https://slack.dev/bolt-python/),
registered as a Slack "Agent" (the newer Agents & AI Apps surface, not a classic
slash-command bot). It runs as a local process connected to Slack over Socket Mode (a
persistent outbound WebSocket, no public URL needed). On each user turn, it:

1. Receives the message via a Bolt event listener.
2. Spins up an MCP (Model Context Protocol) client session that launches a second local
   process, `cleary-mcp`, over stdio.
3. Asks that MCP server what tools it exposes, converts their JSON schemas into function
   declarations for Gemini 2.5 Flash (hosted on Vertex AI).
4. Sends the user's message plus those tool declarations to Gemini, which decides
   whether and which tool(s) to call.
5. Executes any requested tool calls against the live MCP session, feeds the structured
   results back to Gemini, and loops until Gemini produces a final answer with no more
   tool calls.
6. Streams that answer into Slack as visible "task card" steps (one per tool call) plus
   a final text answer, and, if a rewrite was proposed, attaches Block Kit buttons that
   only take action when a human clicks them.

---

## 2. Why MCP, specifically (plain language)

You could imagine building Cleary by just writing all four accessibility checks directly
inside the Slack bot's code. That would work, but it would tightly couple the
"accessibility brain" to Slack. Instead, Cleary keeps those checks in a completely
separate program that knows nothing about Slack at all. The Slack bot and that program
talk to each other using a shared, standard protocol (MCP) instead of custom code glued
together. That means the accessibility checks could be reused by a completely different
chat app, or a command-line tool, or anything else that speaks MCP, without changing a
single line of the checking logic itself.

## 2a. Why MCP, specifically (technical)

MCP (Model Context Protocol) standardizes the interface between an LLM-calling client and
a tool-providing server: `list_tools()` returns tool names, descriptions, and JSON
Schema input schemas; `call_tool(name, args)` executes one and returns structured
content. Because it's a protocol rather than a library import, the server can run in a
separate process, a separate language, or on a separate machine, and the client only
needs a transport (here, stdio) and the two RPC calls above. This repo uses the official
`mcp` Python SDK on both sides: `mcp.server.fastmcp.FastMCP` on the server
(`cleary-mcp/server.py`) and `mcp.client.stdio.stdio_client` /
`mcp.ClientSession` on the client (`agent/listeners/assistant/mcp_client.py`).

---

## 3. Architecture

```
Slack side panel  (HOST)
        |  Bolt Events / Web API
        v
agent/  (CLIENT)  -- Gemini 2.5 Flash reasons here
        |  MCP over stdio
        v
cleary-mcp/  (SERVER)  -- four pure-function accessibility tools
```

- **Host**: Slack itself. Renders the conversation, the task-card UI (Slack's newer
  streaming chat surface for Agents), and Block Kit buttons.
- **Client**: `agent/`, a Bolt for Python app. Its job is the whole "agent loop": call
  the LLM, notice when it wants a tool, call the tool via MCP, feed the result back,
  repeat, then render the final answer.
- **Server**: `cleary-mcp/`, a `FastMCP` process. It has zero Slack-specific code. It
  receives plain text or plain data structures in, and returns plain dicts out.

### Key files

| File | Role |
|---|---|
| `agent/app.py` | Entry point; starts the Bolt app over Socket Mode |
| `agent/listeners/assistant/message.py` | Handles a user turn in the side panel; calls the LLM, attaches rewrite/feedback blocks |
| `agent/listeners/assistant/mcp_client.py` | The actual MCP client + Gemini tool-calling loop |
| `agent/listeners/actions/actions.py` | Handles button clicks (`copy_rewrite`, `post_rewrite`, feedback) |
| `agent/listeners/views/rewrite_block.py` | Builds the Copy/Post rewrite Block Kit buttons |
| `agent/manifest.json` | Slack app manifest: scopes, events, assistant description |
| `cleary-mcp/server.py` | The MCP server; all four accessibility tools live here |

---

## 4. The four tools

Each tool is a plain Python function decorated with `@mcp.tool()`. FastMCP
auto-generates a JSON Schema from the function's type hints, and the function's
docstring becomes the tool's description, which is the *only* thing the LLM sees when
deciding whether to call it. That means the docstring is a user-facing interface, not
just internal documentation.

### `readability_score(text)`

**Plain language**: tells you how hard something is to read, using the same kind of
grade-level score teachers use to pick books for a classroom.

**Technical**: wraps the [`textstat`](https://pypi.org/project/textstat/) library's
`flesch_kincaid_grade` (US school grade level) and `flesch_reading_ease` (0-100, higher
is easier) functions. Returns a dict with both scores, a plain-language verdict string,
and a `target_grade` of 8 (a common plain-language writing target).

### `find_jargon(text)`

**Plain language**: spots acronyms and buzzwords that not everyone will understand.

**Technical**: a regex `\b[A-Z]{2,}\b` finds all-caps runs of 2+ letters, filtered
against a small allowlist (`OK`, `FAQ`, `CEO`, etc.) of acronyms common enough not to
flag. A second pass does a case-insensitive substring match against a hardcoded list of
~18 workplace jargon phrases (`leverage`, `circle back`, `boil the ocean`, ...). Both are
deliberately simple heuristics, not an ML model, since precision on obvious cases beats
an opaque classifier for a hackathon scope.

### `alt_text_check(message_blocks)`

**Plain language**: looks at images in a message and flags ones that don't have a
meaningful description for people who use screen readers.

**Technical**: recursively walks a Slack Block Kit `blocks` array (images can be
nested inside other block types), collects every block with `"type": "image"`, and
flags any whose `alt_text` is empty, whitespace, or a generic placeholder
(`"image"`, `"screenshot"`, etc.) that doesn't actually describe the image.

### `cognitive_load_check(text)`

**Plain language**: catches formatting problems that make text extra hard to process
for people with dyslexia or ADHD, things like giant unbroken paragraphs, ALL CAPS
shouting, or long messages with no structure or summary.

**Technical**: four independent heuristics, each threshold-based:
- Wall of text: a single paragraph (split on blank lines) with >= 60 words and no
  internal line breaks.
- Shouting: regex `\b[A-Z]{2,}(?:\s+[A-Z]{2,}){1,}\b` matches runs of 2+ consecutive
  all-caps words.
- No structure: >= 120 total words with no bullet/numbered markers and fewer than 2
  newlines.
- No summary: >= 150 total words with no `TL;DR`/`Summary`/`In short` lead-in.

All four tools return a JSON-serializable dict with a `verdict` key. That verdict is
what feeds directly into the deterministic "impact line" the agent shows the user (see
section 6), separately from whatever the LLM decides to say in prose.

---

## 5. The agent loop, step by step (technical)

This is the core of `agent/listeners/assistant/mcp_client.py::run_agent_turn`:

1. Open a `stdio_client` connection that spawns `cleary-mcp/server.py` using
   *that project's own virtualenv interpreter* (resolved via relative paths from the
   current file, so it works regardless of where the repo is checked out).
2. `await session.list_tools()`, then convert each tool's `inputSchema` (a MCP-standard
   JSON Schema dict) into a Gemini `FunctionDeclaration` via
   `types.Schema.from_json_schema(json_schema=types.JSONSchema.model_validate(schema),
   api_option="VERTEX_AI")`.
3. Loop up to `MAX_TOOL_ROUNDS` (4) times:
   - Call `client.models.generate_content(model="gemini-2.5-flash", contents=...,
     config=GenerateContentConfig(system_instruction=SYSTEM_PROMPT, tools=gemini_tools))`.
   - Inspect the response's `candidate.content.parts` for `function_call` entries.
   - If none, the model is done: break out of the loop.
   - If there are function calls, for each one: emit a Slack `TaskUpdateChunk` with
     `status="in_progress"`, execute `await session.call_tool(name, args)`, emit a
     second `TaskUpdateChunk` with `status="complete"` (or `"error"` if the tool call
     raised or returned `isError`), and append a `Part.from_function_response(...)` to
     the conversation so Gemini can see the result on the next round.
4. Once the loop ends, join all accumulated text across rounds, strip
   `<<<REWRITE>>> ... <<<END REWRITE>>>` markers (see section 6) out of the display
   text while extracting their contents separately, and stream the cleaned text into
   Slack via `streamer.append(markdown_text=...)`.
5. Return the extracted rewrite text (or `None`) up to `message.py`, which attaches
   Copy/Post rewrite buttons only if a rewrite exists.

This design means the *conversation loop* (steps 2-4) is generic MCP + Gemini
tool-calling; none of it is aware that the tools happen to be about accessibility.
Swapping `cleary-mcp` for a completely different MCP server would require no changes to
this file at all.

---

## 6. Human-in-the-loop: rewrite markers and buttons

The system prompt instructs Gemini: whenever it proposes an actual rewrite (not just an
explanation), wrap *only* the rewritten text between `<<<REWRITE>>>` and
`<<<END REWRITE>>>` markers. The client extracts that span via a regex
(`_extract_rewrite` in `mcp_client.py`), strips the markers from what's shown in chat
(so the user never sees literal marker tokens, just the rewrite inline as normal
prose), and separately returns the raw rewrite text.

`message.py` then does:

```python
rewrite = call_llm(streamer, prompts)
blocks = (create_rewrite_block(rewrite) if rewrite else []) + create_feedback_block()
streamer.stop(blocks=blocks)
```

`create_rewrite_block` (in `agent/listeners/views/rewrite_block.py`) builds a Block Kit
`ActionsBlock` with two buttons, `copy_rewrite` and `post_rewrite`, each carrying the
rewrite text as its `value` (capped at 2000 characters). The corresponding handlers in
`agent/listeners/actions/actions.py`:

- `handle_copy_rewrite`: posts an *ephemeral* message (visible only to the clicking
  user) with the rewrite text in a code block, so they can select and copy it manually
  (Slack has no true clipboard-write API).
- `handle_post_rewrite`: posts a real message into the same thread, explicitly
  attributed to the user who clicked ("Rewrite posted by @user: ..."), so there's a
  visible audit trail that a human, not the bot, chose to publish it.

Neither handler runs unless a human clicks a button. The agent itself never calls
`chat_postMessage` with the rewrite on its own initiative.

The "impact line" (e.g. "reading grade 45.6, aim for grade 8 or below") is *not*
generated by the LLM. It's computed deterministically in `_impact_line()` directly from
a tool's JSON result, independent of how the model chooses to phrase its explanation.
This guarantees the concrete number is always accurate and always present, rather than
depending on the model remembering to mention it.

---

## 7. The LLM: Gemini 2.5 Flash on Vertex AI

Cleary's reasoning model is `gemini-2.5-flash`, called through the `google-genai` SDK
with `genai.Client(vertexai=True, project=..., location=...)`. Authentication uses
`gcloud`'s Application Default Credentials (`gcloud auth application-default login`),
not an API key. This was a mid-project pivot: the original design targeted Claude, and
the switch happened after hitting an Anthropic billing limit with no budget to resolve
it. Because the MCP tool-calling loop is a generic pattern (list tools, convert
schemas, call, feed results back), most of the actual rewrite involved was the schema
conversion step: Claude's tool-use content blocks and Gemini's `FunctionDeclaration` /
`Schema.from_json_schema` are shaped differently, but the MCP server itself, and the
concept of the loop, didn't need to change.

---

## 8. Extending Cleary

To add a fifth tool:

1. Write a plain function in `cleary-mcp/server.py`, decorate it `@mcp.tool()`, and
   write a clear docstring, since that's the only thing the LLM sees to decide when to
   call it.
2. Return a JSON-serializable dict, ideally including a `verdict` key so the impact-line
   logic can pick it up.
3. If you want a deterministic impact line for it, add a branch to `_impact_line()` in
   `agent/listeners/assistant/mcp_client.py`.
4. Nothing else changes. `list_tools()` will pick the new tool up automatically, and
   Gemini will see it the next time a session starts.

---

## 9. Known limitations

- The agent only responds to `@mentions` or messages inside its own side panel, not
  every message in a channel (no `message.channels` event subscription). This was a
  deliberate scope decision, not an oversight, to avoid the bot passively reading every
  channel message.
- `find_jargon`, `alt_text_check`, and `cognitive_load_check` are heuristic (regex,
  allowlists, word counts), not machine-learned models. Good enough for a demo, not a
  production-grade accessibility auditor.
- Vertex AI model availability is project- and region-specific. `gemini-2.5-flash` was
  the model confirmed available on the test project/region; other projects may need a
  different model ID in `agent/listeners/assistant/mcp_client.py`.
