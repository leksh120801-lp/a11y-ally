# Part 1: The Slack Message Nobody Can Read

There's a particular kind of Slack message everyone has seen. It's one giant paragraph.
It's got at least four acronyms nobody's ever defined. Somewhere in the middle, someone
starts SHOUTING IN ALL CAPS about a deadline. And if there's a screenshot attached, good
luck if you're using a screen reader, because there's a decent chance it has no
description at all.

Nobody means to write an inaccessible message. It just happens, because the person
writing it can read it fine. The cost lands somewhere else entirely: on the teammate with
dyslexia who has to read that wall of text three times, on the person for whom English
is a second language trying to parse the jargon, on the screen-reader user who just hears
"image" and has no idea what they're missing.

That invisible cost is what we built Cleary to catch.

## What Cleary actually does

Cleary is a Slack agent, meaning it lives in Slack's dedicated Agents side panel, the
same kind of interface you'd use to chat with any AI assistant built into Slack. You open
it, and it greets you with three things it can help with:

- "Make this plain-language" — paste some dense text, get back a simpler version.
- "Check this thread for accessibility issues" — point it at a conversation.
- "Does this image have alt text?" — ask about images in a message.

Under the hood, it checks four specific things:

1. **How hard is this to read?** Using the same grade-level scoring system that's been
   used to design textbooks for decades, it tells you exactly how much education someone
   would need to parse your sentence. Test it on real corporate writing sometime.
   The numbers get uncomfortable fast.
2. **Is there unexplained jargon?** Acronyms, buzzwords, the kind of shorthand that feels
   invisible to the person who uses it every day and completely opaque to someone new.
3. **Do images have alt text?** Not just *any* alt text, either, a lot of tools will
   accept "image.png" as a valid description and call it done. Cleary specifically flags
   generic placeholders that don't actually describe anything.
4. **Is this exhausting to process?** This one's newer and, honestly, the one we're
   proudest of. It catches walls of text with zero paragraph breaks, ALL-CAPS shouting,
   and long messages with no summary or structure, the specific things that make text
   disproportionately harder for people with dyslexia or ADHD, even when the words
   themselves aren't complicated.

When it finds something, it doesn't just complain. It shows you exactly why it matters,
in plain terms, "reading grade 45, aim for grade 8 or below", and then it offers an
actual rewrite. Not a rephrase. An actual restructuring: shorter sentences, a summary up
top, bullet points instead of one unbroken block, the shouting turned back into normal
sentences.

## The part we think matters most: it never acts on its own

Here's the thing about a lot of "accessibility helper" tools: they either auto-correct
silently, which is unsettling and sometimes wrong, or they're a separate audit dashboard
nobody opens because it's not where the actual writing happens.

Cleary does neither. It reviews content only when asked. When it has a fix to suggest,
it shows two buttons: **Copy rewrite** and **Post rewrite**. Nothing happens until a
human clicks one. If you click "Post rewrite," it posts the fix into the same thread,
clearly labeled as posted by you. If you just want to grab the text and paste it
somewhere yourself, "Copy rewrite" shows it to you in a way you can easily select and
copy.

That's a deliberate choice, not a missing feature. An accessibility tool that silently
rewrites your words erodes trust fast, and it can get things wrong in ways that are
worse than the original problem. A tool that explains the problem, shows you the fix,
and lets you decide, builds the habit of writing accessibly in the first place, instead
of outsourcing it to a black box.

## Why we built it this way

This was built for Slack's "Agent for Good" hackathon, specifically the accessibility
track, with one hard technical requirement: it had to be a real MCP (Model Context
Protocol) integration, not just an LLM wrapper. That constraint turned out to shape a lot
of the actual design, which is the part we get into in [Part 2](./02-how-cleary-is-built-mcp-architecture.md):
how Cleary is structured as three genuinely separate pieces, a Slack host, a Bolt agent
acting as an MCP client, and a completely standalone accessibility server that has no
idea Slack exists at all.
