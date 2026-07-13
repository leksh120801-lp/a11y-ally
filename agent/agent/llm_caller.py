import asyncio

from slack_sdk.web.chat_stream import ChatStream

from listeners.assistant.mcp_client import run_agent_turn


def call_llm(streamer: ChatStream, prompts: list[dict]) -> str | None:
    """Run an Cleary agent turn (Gemini reasoning + a11y-mcp tool calls) and stream the result.

    Returns the suggested rewrite text if the model proposed one, else None.
    """
    return asyncio.run(run_agent_turn(streamer, prompts))
