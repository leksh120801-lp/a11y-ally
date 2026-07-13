"""cleary-mcp: an MCP server exposing accessibility-review tools for Slack content.

Host = Slack (the side panel) | Client = the Bolt agent | Server = this process.
Tools here do the actual accessibility analysis; the agent's LLM decides when to
call them and how to present the results to the user.
"""

import re

import textstat
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cleary-mcp")

# Common workplace jargon/buzzwords that hurt plain-language readability even
# when they aren't acronyms.
_JARGON_PHRASES = [
    "synergy",
    "synergize",
    "leverage",
    "bandwidth",
    "actionable",
    "circle back",
    "low-hanging fruit",
    "boil the ocean",
    "paradigm shift",
    "deep dive",
    "touch base",
    "move the needle",
    "double-click",
    "socialize this",
    "table this",
    "ping me",
    "north star",
    "best-in-class",
]

# Acronyms so common they aren't worth flagging as jargon.
_ACRONYM_ALLOWLIST = {"I", "A", "OK", "US", "UK", "EU", "CEO", "FAQ", "ASAP"}

_GENERIC_ALT_TEXT = {"", "image", "photo", "picture", "img", "screenshot", "graphic"}

_WALL_OF_TEXT_WORDS = 60  # words in a single unbroken paragraph
_LONG_MESSAGE_WORDS = 120  # total words before we expect some structure
_TLDR_THRESHOLD_WORDS = 150  # total words before we expect a summary up top
_SHOUTY_PATTERN = re.compile(r"\b[A-Z]{2,}(?:\s+[A-Z]{2,}){1,}\b")
_BULLET_PATTERN = re.compile(r"(?m)^\s*([-*•]|\d+[.)])\s")
_SUMMARY_LEAD_PATTERN = re.compile(r"^\s*(tl;?dr|summary|tldr|in short)\b", re.IGNORECASE)


@mcp.tool()
def readability_score(text: str) -> dict:
    """Score the readability of a piece of text.

    Computes the Flesch-Kincaid grade level (the US school grade needed to
    understand the text) and the Flesch reading ease score (0-100, higher is
    easier), then gives a plain-language verdict.

    Args:
        text: The message, thread, or canvas content to analyze.

    Returns:
        A dict with:
        - grade_level: float, Flesch-Kincaid grade level
        - reading_ease: float, Flesch reading ease score (0-100)
        - verdict: str, plain-language summary of whether this is easy to read
        - target_grade: int, the recommended grade level to aim for (8)
    """
    if not text or not text.strip():
        return {
            "grade_level": 0.0,
            "reading_ease": 100.0,
            "verdict": "No text provided.",
            "target_grade": 8,
        }

    grade_level = textstat.flesch_kincaid_grade(text)
    reading_ease = textstat.flesch_reading_ease(text)

    if grade_level <= 8:
        verdict = f"Easy to read (grade {grade_level:.1f}). Good for a general audience."
    elif grade_level <= 12:
        verdict = f"Moderately difficult (grade {grade_level:.1f}). Consider shortening sentences."
    else:
        verdict = f"Hard to read (grade {grade_level:.1f}). Likely needs a plain-language rewrite."

    return {
        "grade_level": round(grade_level, 1),
        "reading_ease": round(reading_ease, 1),
        "verdict": verdict,
        "target_grade": 8,
    }


@mcp.tool()
def find_jargon(text: str) -> dict:
    """Find likely acronyms and workplace jargon in a piece of text.

    Flags all-caps acronyms (2+ letters, excluding a small allowlist of very
    common ones like OK/FAQ/CEO) and known jargon/buzzword phrases that can
    confuse readers unfamiliar with them.

    Args:
        text: The message, thread, or canvas content to analyze.

    Returns:
        A dict with:
        - acronyms: list of distinct acronyms found, in the order encountered
        - jargon_phrases: list of distinct jargon phrases found
        - verdict: str, plain-language summary
    """
    if not text or not text.strip():
        return {"acronyms": [], "jargon_phrases": [], "verdict": "No text provided."}

    found_acronyms = []
    for match in re.finditer(r"\b[A-Z]{2,}\b", text):
        acronym = match.group()
        if acronym not in _ACRONYM_ALLOWLIST and acronym not in found_acronyms:
            found_acronyms.append(acronym)

    lowered = text.lower()
    found_jargon = [phrase for phrase in _JARGON_PHRASES if phrase in lowered]

    total = len(found_acronyms) + len(found_jargon)
    if total == 0:
        verdict = "No acronyms or jargon detected."
    else:
        verdict = (
            f"Found {len(found_acronyms)} acronym(s) and {len(found_jargon)} "
            "jargon phrase(s) that may need explaining or rewriting."
        )

    return {
        "acronyms": found_acronyms,
        "jargon_phrases": found_jargon,
        "verdict": verdict,
    }


@mcp.tool()
def alt_text_check(message_blocks: list) -> dict:
    """Check Slack Block Kit blocks for images missing meaningful alt text.

    Looks for "image" blocks (top-level or nested inside other block types)
    and flags any whose alt_text is missing, blank, or a generic placeholder
    (e.g. "image", "photo", "screenshot") that doesn't actually describe the
    image content.

    Args:
        message_blocks: A list of Slack Block Kit block dicts, as returned by
            the Slack API for a message (e.g. message["blocks"]).

    Returns:
        A dict with:
        - total_images: int, number of image blocks found
        - missing_alt_text: list of dicts describing each flagged image
          (block_id and image_url when available)
        - verdict: str, plain-language summary
    """
    if not message_blocks:
        return {
            "total_images": 0,
            "missing_alt_text": [],
            "verdict": "No blocks provided.",
        }

    def walk(blocks):
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "image":
                yield block
            for value in block.values():
                if isinstance(value, list):
                    yield from walk(value)

    images = list(walk(message_blocks))
    flagged = []
    for image in images:
        alt_text = (image.get("alt_text") or "").strip().lower()
        if alt_text in _GENERIC_ALT_TEXT:
            flagged.append(
                {
                    "block_id": image.get("block_id"),
                    "image_url": image.get("image_url") or image.get("slack_file"),
                }
            )

    if not images:
        verdict = "No images found."
    elif not flagged:
        verdict = f"All {len(images)} image(s) have descriptive alt text."
    else:
        verdict = f"{len(flagged)} of {len(images)} image(s) are missing meaningful alt text."

    return {
        "total_images": len(images),
        "missing_alt_text": flagged,
        "verdict": verdict,
    }


@mcp.tool()
def cognitive_load_check(text: str) -> dict:
    """Check text for issues that increase cognitive load, especially for
    readers with dyslexia or ADHD.

    Flags long unbroken "wall of text" paragraphs, shouty ALL-CAPS runs,
    long messages with no bullet/numbered structure, and long messages with
    no summary/TL;DR at the top.

    Args:
        text: The message, thread, or canvas content to analyze.

    Returns:
        A dict with:
        - word_count: int, total word count
        - issues: list of str, one entry per issue found
        - verdict: str, plain-language summary
    """
    if not text or not text.strip():
        return {"word_count": 0, "issues": [], "verdict": "No text provided."}

    words = text.split()
    word_count = len(words)
    issues = []

    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    for paragraph in paragraphs:
        paragraph_words = paragraph.split()
        has_line_breaks = "\n" in paragraph.strip()
        if len(paragraph_words) >= _WALL_OF_TEXT_WORDS and not has_line_breaks:
            issues.append(
                f"Wall of text: a {len(paragraph_words)}-word paragraph with no line breaks."
            )
            break

    if _SHOUTY_PATTERN.search(text):
        issues.append("ALL-CAPS run(s) found — reads as shouting and is harder to scan.")

    has_structure = bool(_BULLET_PATTERN.search(text)) or text.count("\n") >= 2
    if word_count >= _LONG_MESSAGE_WORDS and not has_structure:
        issues.append(
            f"Long message ({word_count} words) with no bullets, numbering, or line breaks."
        )

    if word_count >= _TLDR_THRESHOLD_WORDS and not _SUMMARY_LEAD_PATTERN.match(text.strip()):
        issues.append("Long message with no summary/TL;DR at the top.")

    if not issues:
        verdict = "No cognitive-load issues detected."
    else:
        verdict = f"Found {len(issues)} issue(s) that make this harder to scan and process."

    return {
        "word_count": word_count,
        "issues": issues,
        "verdict": verdict,
    }


if __name__ == "__main__":
    mcp.run()
