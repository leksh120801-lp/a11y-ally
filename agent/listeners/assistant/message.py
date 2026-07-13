from logging import Logger

from slack_bolt import BoltContext, Say, SetStatus
from slack_sdk import WebClient

from agent.llm_caller import call_llm
from listeners.views.feedback_block import create_feedback_block
from listeners.views.rewrite_block import create_rewrite_block


def message(
    client: WebClient,
    context: BoltContext,
    logger: Logger,
    message: dict,
    payload: dict,
    say: Say,
    set_status: SetStatus,
):
    """
    Handles when users send messages or select a prompt in an assistant thread and generate AI responses:

    Args:
        client: Slack WebClient for making API calls
        context: Bolt context containing channel and thread information
        logger: Logger instance for error tracking
        payload: Event payload with message details (channel, user, text, etc.)
        say: Function to send messages to the thread
        set_status: Function to update the assistant's status
    """
    try:
        channel_id = payload["channel"]
        team_id = context.team_id
        thread_ts = payload["thread_ts"]
        user_id = context.user_id

        set_status(
            status="thinking...",
            loading_messages=[
                "Checking readability…",
                "Scanning for jargon and acronyms…",
                "Looking for missing alt text…",
                "Drafting a plain-language rewrite…",
            ],
        )

        streamer = client.chat_stream(
            channel=channel_id,
            recipient_team_id=team_id,
            recipient_user_id=user_id,
            thread_ts=thread_ts,
            task_display_mode="timeline",
        )
        prompts: list[dict] = [
            {
                "role": "user",
                "content": message["text"],
            },
        ]
        rewrite = call_llm(streamer, prompts)

        blocks = (create_rewrite_block(rewrite) if rewrite else []) + create_feedback_block()
        streamer.stop(blocks=blocks)

    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
