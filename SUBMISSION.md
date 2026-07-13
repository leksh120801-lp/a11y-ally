# Devpost submission package — Cleary

Copy/paste each section into the matching Devpost field. Human steps (things I can't do
for you) are marked **[HUMAN STEP]**.

---

## Project name

Cleary

## Elevator pitch

Cleary reviews Slack messages, threads, and canvases for accessibility problems —
hard-to-read text, jargon, images missing alt text, and content that's overwhelming for
dyslexic or ADHD readers — and suggests a fix. Every rewrite is human-approved before it
ever gets posted.

## Text description (features / functionality)

Cleary is a Slack agent that lives in the Agents side panel. On request, it reviews a
message, thread, or canvas and checks four things: reading difficulty (Flesch-Kincaid
grade level), jargon/unexplained acronyms, images missing meaningful alt text, and
cognitive-load issues that specifically hurt dyslexic or ADHD readers (walls of text,
ALL-CAPS shouting, no structure, no summary). It shows its work as visible task-card
steps while it calls each check, states the impact in plain terms (e.g. "reading grade
14 — aim for 8 or below"), and — when there's a fix to suggest — proposes an actual
restructured rewrite (shorter sentences, bullets instead of a wall of text, a TL;DR up
top, jargon spelled out). Nothing is ever posted or edited automatically: every rewrite
comes with **Copy rewrite** / **Post rewrite** buttons, and the agent only acts after a
human clicks one.

Under the hood, the four accessibility checks are not baked into the agent — they're
tools exposed by a separate custom MCP server (`cleary-mcp`) that the Slack agent talks
to as an MCP client. Slack is the host, the Bolt agent is the client, and `cleary-mcp` is
a standalone process that has no idea Slack exists.

## Impact ("Slack Agent for Good" track)

Dense, jargon-heavy, wall-of-text messages are a daily, invisible barrier: for people
with dyslexia or ADHD, for non-native English speakers, for anyone reading quickly on a
phone, and for screen-reader users when images have no alt text. Most of the time nobody
notices, because the person who wrote the message can read it fine — the cost lands on
whoever's on the other end.

Cleary makes that cost visible and actionable, on request, without taking control away
from the person who wrote the message. It doesn't silently rewrite anyone's words or
police how people write — it flags the specific problem, explains the impact in concrete
terms, and offers a fix that a human has to actively choose to use. That human-in-the-loop
design is deliberate: accessibility tools that auto-edit content erode trust and can
misfire; a tool that suggests and explains builds the habit of writing more accessibly in
the first place.

## Built with (tags)

slack, accessibility, a11y, mcp, model-context-protocol, ai-agent, agent-for-good,
python, slack-bolt, gemini, vertex-ai, google-cloud, llm, dyslexia, adhd, plain-language,
readability, textstat, nlp, socket-mode

## "Try it out" links

- Repo: https://github.com/leksh120801-lp/cleary
- Slack developer sandbox URL: **[HUMAN STEP — fill in your workspace URL]**

## About the project (Markdown)

### Inspiration

Dense corporate writing, unexplained acronyms, and images with no alt text are a
constant, low-grade accessibility tax that most people never notice paying — or causing.
We wanted something that surfaces that cost in the exact place it happens (a Slack
message, mid-conversation) rather than as a separate audit tool nobody opens.

### What it does

Cleary reviews Slack content on request and checks four things: readability
(Flesch-Kincaid grade level), jargon/acronyms, missing image alt text, and cognitive-load
issues that specifically affect dyslexic/ADHD readers (walls of text, shouting,
no structure, no summary). When it finds something worth fixing, it proposes an actual
restructured rewrite — not just a rephrase — with **Copy rewrite** / **Post rewrite**
buttons. It never posts or edits anything without an explicit human click.

### How we built it

The required hackathon technology was MCP server integration, so we built Cleary
strictly around that framing: Slack is the **host**, a Bolt for Python agent is the
**client**, and the four accessibility checks live in a separate custom MCP server,
`cleary-mcp`, built with the official Python MCP SDK. The agent starts `cleary-mcp` as a
subprocess over stdio, lists its tools, and converts their JSON schemas into function
declarations for the reasoning model — Gemini 2.5 Flash on Vertex AI — which decides when
to call which tool. Tool results flow back to Gemini, which produces a final answer that
gets streamed into Slack as visible task-card steps, followed by an impact line computed
directly from the tool's structured output (not left to the model's phrasing) and, where
relevant, a rewrite with human-approval buttons built with Block Kit.

### Challenges we ran into

We originally built the reasoning step against Claude, matching the "receive input →
reason (Claude) → call MCP tools" framing from our own design doc — then hit an Anthropic
billing wall partway through. Rather than pay for a hackathon project, we pivoted to
Gemini on Vertex AI, authenticated via `gcloud` Application Default Credentials instead
of an API key. That meant rewriting the tool-calling loop against a different
function-calling schema format (Gemini's `Schema.from_json_schema` vs. Claude's
tool-use blocks) — a good reminder that the MCP layer is what actually matters for
portability: swapping the reasoning model out barely touched the MCP server at all.

### Accomplishments that we're proud of

Getting a real, working MCP tool-use loop end to end — Gemini deciding when to call
`readability_score` vs. `cognitive_load_check`, executing them against a live subprocess,
and feeding results back — and getting the rewrite step to actually *restructure* content
(bullets, de-shouted text, a TL;DR) rather than just producing plainer prose.

### What we learned

How much of "the agent" is really the MCP client's plumbing rather than the LLM prompt —
schema conversion, subprocess lifecycle, and tool-result formatting mattered more to
getting a reliable demo than prompt wording did.

### What's next

A `message.channels` scope so it can proactively flag issues in channels it's invited to
(not just on request), and swapping the heuristic jargon/cognitive-load checks for
something closer to an actual readability/accessibility model.

---

## Devpost checklist — status

- [x] Project name, elevator pitch, description, impact statement — drafted above
- [x] Architecture diagram (PNG) — `agent/assets/architecture_diagram.png`
- [x] Demo video script (~3 min, narrates MCP host/client/server roles) — `DEMO_SCRIPT.md`
- [x] Tags — drafted above
- [x] "Try it out" repo link
- [ ] **[HUMAN STEP]** Record and upload the ~3 min demo video (follow `DEMO_SCRIPT.md`)
- [ ] **[HUMAN STEP]** Slack developer sandbox URL
- [ ] **[HUMAN STEP]** Grant workspace/app access to `slackhack@salesforce.com` and
      `testing@devpost.com` — see checklist below
- [ ] **[HUMAN STEP]** Image gallery screenshots (up to 15, JPG/PNG/GIF, 3:2 ratio ideal)
- [ ] **[HUMAN STEP]** Paste everything above into the actual Devpost submission form

### Granting access to the judges — do this yourself

1. In your Slack sandbox workspace: **Settings & administration → Manage members →
   Invite people**, invite `slackhack@salesforce.com` and `testing@devpost.com` as
   members so they can see/use the installed app.
2. In your Slack app config (api.slack.com/apps → your app → **Collaborators**), add
   both emails as collaborators if you want them able to inspect the app config itself.
3. Double check neither invite requires an admin approval step that could miss the
   deadline — send these early.

### Suggested screenshots for the image gallery

1. The Agents sidebar showing Cleary with its greeting + three suggested prompts
2. A `readability_score` task-card step mid-flight ("Calling readability_score...")
3. A finished response with the impact line and grade level visible
4. The Copy rewrite / Post rewrite buttons under a suggested rewrite
5. A restructured rewrite (bullets + TL;DR) next to the original wall-of-text input
6. The `architecture_diagram.png` itself (also works as a gallery image, not just the
   required upload)
