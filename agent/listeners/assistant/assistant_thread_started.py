from logging import Logger

from slack_bolt import Say, SetSuggestedPrompts


def assistant_thread_started(
    say: Say,
    set_suggested_prompts: SetSuggestedPrompts,
    logger: Logger,
):
    """
    Handle the assistant thread start event by greeting the user and setting suggested prompts.

    Args:
        say: Function to send messages to the thread from the app
        set_suggested_prompts: Function to configure suggested prompt options
        logger: Logger instance for error tracking
    """
    try:
        say("Hi! I'm Cleary. I review Slack content for accessibility issues and suggest plain-language rewrites — I never post or edit anything without your say-so.")
        set_suggested_prompts(
            prompts=[
                {
                    "title": "Make this plain-language",
                    "message": "Make this plain-language: ",
                },
                {
                    "title": "Check this thread for accessibility issues",
                    "message": "Check this thread for accessibility issues.",
                },
                {
                    "title": "Does this image have alt text?",
                    "message": "Does this image have alt text?",
                },
            ]
        )
    except Exception as e:
        logger.exception(f"Failed to handle an assistant_thread_started event: {e}", e)
        say(f":warning: Something went wrong! ({e})")
