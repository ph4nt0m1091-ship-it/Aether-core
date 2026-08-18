class ResiliencePolicy:
    """
    Classifies provider failures and determines
    whether an operation may be retried safely.

    This policy is intentionally conservative.

    AI generation may be retried.

    Destructive or state-changing actions are
    never blindly retried here.
    """

    RETRYABLE_ERROR_WORDS = (
        "timed out",
        "timeout",
        "temporarily unavailable",
        "connection reset",
        "connection refused",
        "remote end closed",
        "server disconnected",
        "service unavailable",
        "try again",
        "resource busy"
    )

    NON_RETRYABLE_ERROR_WORDS = (
        "not installed",
        "unsupported",
        "not found",
        "no prompt",
        "no model",
        "invalid",
        "permission",
        "blocked"
    )

    SAFE_RETRY_CAPABILITIES = (
        "generate_text",
        "list_models",
        "warm_model"
    )

    # ---------------------------------
    # RETRY DECISION
    # ---------------------------------

    def can_retry(
        self,
        capability,
        result
    ):

        if capability not in self.SAFE_RETRY_CAPABILITIES:

            return False

        if result.get(
            "success",
            False
        ):

            return False

        error = str(
            result.get(
                "error",
                ""
            )
        ).lower()

        if not error:

            return False

        for phrase in self.NON_RETRYABLE_ERROR_WORDS:

            if phrase in error:

                return False

        for phrase in self.RETRYABLE_ERROR_WORDS:

            if phrase in error:

                return True

        return False

    # ---------------------------------
    # FAILURE CATEGORY
    # ---------------------------------

    def classify(
        self,
        result
    ):

        if result.get(
            "success",
            False
        ):

            return "success"

        error = str(
            result.get(
                "error",
                ""
            )
        ).lower()

        for phrase in self.NON_RETRYABLE_ERROR_WORDS:

            if phrase in error:

                return "permanent"

        for phrase in self.RETRYABLE_ERROR_WORDS:

            if phrase in error:

                return "temporary"

        return "unknown"