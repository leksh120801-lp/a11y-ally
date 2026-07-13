from slack_bolt import App

from .actions import handle_copy_rewrite, handle_feedback, handle_post_rewrite


def register(app: App):
    app.action("feedback")(handle_feedback)
    app.action("copy_rewrite")(handle_copy_rewrite)
    app.action("post_rewrite")(handle_post_rewrite)
