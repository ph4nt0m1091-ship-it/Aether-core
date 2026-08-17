class PermissionManager:
    """
    Manages pending user approvals for Aether.

    Only one action can be pending at a time
    in this initial implementation.
    """

    APPROVE_WORDS = {
        "yes",
        "y",
        "approve",
        "approved",
        "confirm",
        "do it",
        "run it",
        "go ahead"
    }

    DENY_WORDS = {
        "no",
        "n",
        "deny",
        "cancel",
        "stop",
        "never mind",
        "nevermind"
    }

    def __init__(self):

        self.pending = None

    # ---------------------------------
    # CREATE REQUEST
    # ---------------------------------

    def request(
        self,
        action,
        data
    ):

        self.pending = {
            "action": action,
            "data": data
        }

        return self.pending

    # ---------------------------------
    # STATUS
    # ---------------------------------

    def has_pending(self):

        return self.pending is not None

    def get_pending(self):

        return self.pending

    # ---------------------------------
    # USER RESPONSE
    # ---------------------------------

    def interpret_response(
        self,
        message
    ):

        lower = (
            message
            .strip()
            .lower()
        )

        if lower in self.APPROVE_WORDS:

            return "approve"

        if lower in self.DENY_WORDS:

            return "deny"

        return None

    # ---------------------------------
    # CONSUME
    # ---------------------------------

    def consume(self):

        pending = self.pending

        self.pending = None

        return pending

    # ---------------------------------
    # CANCEL
    # ---------------------------------

    def cancel(self):

        self.pending = None