from slack_sdk.models.blocks import ActionsBlock, Block, ButtonElement

# Slack button action values are capped well above this in practice, but keep
# rewrites well under the limit so the value always round-trips intact.
_MAX_VALUE_LENGTH = 2000


def create_rewrite_block(rewrite_text: str) -> list[Block]:
    """Build human-in-the-loop Copy/Post buttons for a suggested rewrite.

    Never posts or edits anything by itself — the rewrite is only applied
    when a human clicks one of these buttons.
    """
    value = rewrite_text[:_MAX_VALUE_LENGTH]
    return [
        ActionsBlock(
            block_id="rewrite_actions",
            elements=[
                ButtonElement(
                    text="Copy rewrite",
                    action_id="copy_rewrite",
                    value=value,
                ),
                ButtonElement(
                    text="Post rewrite",
                    action_id="post_rewrite",
                    style="primary",
                    value=value,
                ),
            ],
        )
    ]
