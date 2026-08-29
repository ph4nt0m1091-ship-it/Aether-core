class ResiliencePolicy:
    """
    Classifies failures and controls Aether's automatic
    recovery decisions.

    Recovery stays intentionally conservative:

    - Safe temporary operations may be retried once.
    - Only explicitly approved local AI generation may
      use an automatic fallback.
    - Permission-gated, destructive, state-changing,
      cloud, and unknown operations never receive an
      automatic fallback here.
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
        "warm_model",
        "list_processes",
        "research",
        "web_search"
    )

    SAFE_FALLBACK_CAPABILITIES = (
        "generate_text",
    )

    LOCAL_MODEL_FALLBACK_ORDER = {
        "qwen3:8b": (
            "qwen3:4b",
            "gemma3:1b"
        ),
        "qwen3:4b": (
            "gemma3:1b",
        ),
        "gemma3:1b": (
            "qwen3:4b",
        )
    }

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
    # FALLBACK DECISION
    # ---------------------------------

    def fallback_plan(
        self,
        step,
        result
    ):
        """
        Return a deterministic, local-only fallback plan.

        At this layer Aether only falls back between known
        Ollama models for direct local generate_text steps.
        The workflow engine never switches to cloud and
        never invents a new command or capability.
        """

        if result.get(
            "success",
            False
        ):

            return None

        if result.get(
            "paused"
        ):

            return None

        if not isinstance(
            step,
            dict
        ):

            return None

        if step.get(
            "type"
        ) != "provider":

            return None

        capability = step.get(
            "action",
            ""
        )

        if capability not in self.SAFE_FALLBACK_CAPABILITIES:

            return None

        target = str(
            step.get(
                "target",
                ""
            )
            or ""
        ).strip().lower()

        # Automatic fallback is local-only. Requiring the
        # explicit Ollama target prevents a silent route to
        # a different provider, especially cloud.
        if target != "ollama":

            return None

        data = step.get(
            "data",
            {}
        )

        if not isinstance(
            data,
            dict
        ):

            return None

        current_model = str(
            data.get(
                "model",
                ""
            )
            or ""
        ).strip()

        if not current_model:

            return None

        candidates = list(
            self.LOCAL_MODEL_FALLBACK_ORDER.get(
                current_model,
                ()
            )
        )

        if not candidates:

            return None

        error = str(
            result.get(
                "error",
                ""
            )
            or ""
        ).lower()

        for phrase in self.NON_RETRYABLE_ERROR_WORDS:

            if phrase in error:

                return None

        return {
            "provider": "ollama",
            "capability": capability,
            "from_model": current_model,
            "candidates": candidates,
            "reason": (
                "Approved deterministic local-model "
                "fallback after the original step and "
                "its safe retry did not succeed."
            )
        }

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
