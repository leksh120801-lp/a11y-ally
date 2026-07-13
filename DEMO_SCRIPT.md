# A11y Ally — demo script (2–3 min)

Goal: show the accessibility use case working end-to-end, and narrate the MCP
host/client/server roles explicitly, since that's the required hackathon technology.

---

**[0:00–0:20] Hook + the problem**

> "Every day, people post dense, jargon-heavy messages in Slack — hard to read, full of
> acronyms, sometimes images with no alt text. That's invisible to a lot of your
> teammates. Meet A11y Ally — an agent that reviews Slack content for accessibility
> problems and suggests plain-language rewrites, on request, always human-approved."

*(Show the Slack sidebar, click into A11y Ally under Agents.)*

---

**[0:20–0:50] Architecture — narrate the MCP roles explicitly**

> "This is built as an MCP integration, with three distinct pieces. Slack itself — this
> side panel — is the **host**. My Bolt agent, running locally, is the **client**: it's
> the thing that actually talks to Slack and to the LLM. And the accessibility logic
> itself — readability scoring, jargon detection, alt-text checking — lives in a
> completely separate process I built: a custom MCP **server** called a11y-mcp. The
> client starts that server, asks it what tools it has, and calls them over the Model
> Context Protocol whenever the LLM decides it needs one."

*(Optional: briefly show the architecture diagram from the README, or the three folders
in the repo — `agent/`, `a11y-mcp/`.)*

---

**[0:50–1:40] Golden path demo**

> "Let's try it. I'll paste some genuinely bad corporate writing."

*(Type: "Make this plain-language: The utilization of multifaceted methodological
paradigms necessitates a comprehensive reevaluation of preexisting infrastructural
frameworks.")*

> "Watch the task card — it's calling `readability_score` on the a11y-mcp server right
> now, over MCP, live."

*(Point at the task-card step appearing.)*

> "And there's the impact line — reading grade 30, way above the grade-8 target — plus a
> plain-language rewrite. But notice: it hasn't posted anything. It's just a suggestion."

*(Point at the Copy rewrite / Post rewrite buttons.)*

> "I have to explicitly approve it before anything happens."

*(Click "Post rewrite" — show the message landing in the thread.)*

---

**[1:40–2:10] Second tool, image alt text**

*(Paste or reference a message containing an image block, ask: "Does this image have alt
text?")*

> "Same pattern — different tool this time, `alt_text_check`, same MCP server. It tells
> me exactly which images are missing meaningful alt text, again without touching
> anything on its own."

---

**[2:10–2:40] Why this matters + wrap-up**

> "This is 'agent for good' because it's not gatekeeping accessibility behind an
> automated rewrite nobody asked for — it surfaces the problem, explains the impact in
> plain terms, and leaves the decision with a human. And architecturally, it's a clean
> demonstration of MCP: a Slack host, a Bolt client, and a purpose-built accessibility
> server that has literally no idea Slack exists — you could swap the host for a
> different chat app tomorrow and the server wouldn't change at all."

*(End on the repo README's architecture diagram or the GitHub repo page.)*

---

## Notes for recording

- Have a few "bad" text samples ready in a scratch note so you're not typing live.
- Make sure the local `python app.py` process is running and connected before you start
  recording (check for `⚡️ Bolt app is running!` in the terminal).
- If demoing the alt-text check, prepare a test message with an image block ahead of time
  (Slack's composer doesn't make it trivial to attach a *missing*-alt-text image on the
  fly).
