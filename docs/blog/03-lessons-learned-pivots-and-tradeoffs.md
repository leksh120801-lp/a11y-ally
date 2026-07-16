# Part 3: What We'd Do Differently

*Part 3 of the Cleary writeup. [Part 1](./01-the-problem-and-what-cleary-does.md) covers
what it does, [Part 2](./02-how-cleary-is-built-mcp-architecture.md) covers the MCP
architecture. This one is the honest retrospective.*

## The Claude-to-Gemini pivot, and what it actually taught us

The original plan had Claude doing the reasoning, matching the classic "receive input,
reason, call MCP tools" framing almost word for word. Partway into building it, a fresh
Anthropic account hit a billing wall. Rather than pay for a hackathon side project, we
switched the reasoning model to Gemini 2.5 Flash on Vertex AI, funded by free GCP
credits instead, and authenticated through `gcloud` credentials rather than an API key.

We expected that to be a bigger rewrite than it was. It touched exactly one function's
worth of real logic: converting MCP's tool schemas (standard JSON Schema) into whatever
shape a given model's function-calling API wants. Claude's tool-use content blocks and
Gemini's `FunctionDeclaration` objects are shaped differently enough that this couldn't
be a one-line change, but the MCP server itself, the four accessibility tools, the whole
task-card and rewrite-button UI, didn't move at all.

That's the actual lesson: the discipline of building strictly around MCP meant the
reasoning model was genuinely swappable underneath the application, not just in theory.
If we'd built the accessibility checks as inline functions inside a single Claude-specific
prompt, that pivot would have been a rewrite instead of a patch.

## The naming problem nobody warns you about

The project started life as "A11y Ally." Partway through, we renamed it to "Cleary,"
which meant renaming the GitHub repo, the local folder, the internal MCP server package
(`a11y-mcp` to `cleary-mcp`), and every text mention across the codebase. The annoying
part wasn't the code, `grep` and `sed` handle that fine, it was that Python virtualenvs
bake an absolute path into their activation scripts. Moving the folder silently broke
both venvs until we deleted and recreated them from scratch. Small thing, but it cost
real time, and it's the kind of gotcha that's obvious in hindsight and invisible until
you hit it.

## Heuristics over models, on purpose, with a clear cost

All four accessibility checks are heuristic: `textstat`'s readability formulas, regex
patterns for acronyms and shouting, allowlists of jargon phrases, word-count thresholds
for "wall of text." None of it is machine-learned. That was a deliberate scope decision
for a hackathon timeline, not an oversight, but it has a real cost: the jargon detector
can only catch phrases we thought to list, and the cognitive-load thresholds (60 words
for a wall of text, 150 for expecting a summary) are educated guesses, not validated
against real dyslexic or ADHD readers. A production version of this would want actual
user research behind those numbers, not just reasonable-sounding defaults.

## Scope we cut on purpose

The agent only responds when it's directly messaged in its side panel or `@mentioned` in
a channel. It doesn't passively read every message in every channel it's invited to.
That's a genuine tradeoff: it means Cleary can't proactively flag an inaccessible message
the moment it's posted, only when someone thinks to ask. We chose that specifically
because a bot that reads every channel message by default is a much bigger privacy and
scope footprint, and "review on request" fit the human-in-the-loop philosophy better
than "the bot is always watching."

## What we'd build next

- A `message.channels` event subscription, opt-in per channel, so Cleary could
  proactively flag issues without becoming a silent surveillance bot.
- Replacing the jargon and cognitive-load heuristics with something closer to an actual
  trained readability/accessibility model, or at minimum, thresholds informed by real
  research rather than reasonable guesses.
- A shared "impact history" so a team could see, in aggregate, whether their
  accessibility scores are trending better over time, still without ever auto-editing
  anything.

None of that changes the core bet this project made: that the most useful accessibility
tool is the one that explains the problem clearly and then gets out of the way of the
human decision. Everything above is about doing that better, not about doing something
different.
