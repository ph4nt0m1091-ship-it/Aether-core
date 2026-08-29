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
        result,
        preferred_model=None
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

        preferred_model = str(
            preferred_model or ""
        ).strip()

        # Adaptive history may reorder only the already
        # approved local fallback candidates. It cannot
        # add a new model, provider, capability, or cloud
        # route.
        if (
            preferred_model
            and preferred_model in candidates
        ):

            candidates = [
                preferred_model
            ] + [
                model
                for model in candidates
                if model != preferred_model
            ]

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
    # ADAPTIVE RETRY DECISION
    # ---------------------------------

    def adaptive_retry_decision(
        self,
        capability,
        result,
        evidence,
        step=None
    ):
        """
        Decide whether strong local history justifies
        skipping one redundant same-model retry.

        This is intentionally narrow:
        - generate_text only
        - the current error must already be safely retryable
        - the exact failure pattern must have occurred at
          least three times
        - the same approved local fallback model must have
          succeeded at least twice before

        The decision never authorizes a new fallback.
        fallback_plan still enforces the local-only allowlist.
        """

        decision = {
            "skip_retry": False,
            "reason": None,
            "preferred_model": None,
            "repeated_failure_count": 0,
            "preferred_fallback_successes": 0
        }

        if capability != "generate_text":

            return decision

        if not self.can_retry(
            capability,
            result
        ):

            return decision

        if not isinstance(
            evidence,
            dict
        ):

            return decision

        repeated = int(
            evidence.get(
                "repeated_failure_count",
                0
            )
            or 0
        )

        fallback_successes = int(
            evidence.get(
                "preferred_fallback_successes",
                0
            )
            or 0
        )

        preferred_model = str(
            evidence.get(
                "preferred_fallback_model",
                ""
            )
            or ""
        ).strip()

        decision[
            "repeated_failure_count"
        ] = repeated

        decision[
            "preferred_fallback_successes"
        ] = fallback_successes

        decision[
            "preferred_model"
        ] = (
            preferred_model
            or None
        )

        if repeated < 3:

            return decision

        if fallback_successes < 2:

            return decision

        if not preferred_model:

            return decision

        # Adaptive retry skipping is allowed only when the
        # exact step is already eligible for Aether's
        # deterministic local-only fallback policy.
        #
        # This blocks cloud targets, permission failures,
        # destructive/state-changing actions, unsupported
        # capabilities, and unapproved fallback models.
        if not isinstance(
            step,
            dict
        ):

            return decision

        fallback = self.fallback_plan(
            step,
            result,
            preferred_model=preferred_model
        )

        if fallback is None:

            return decision

        if preferred_model not in fallback.get(
            "candidates",
            []
        ):

            return decision

        decision[
            "skip_retry"
        ] = True

        decision[
            "reason"
        ] = (
            "The exact temporary failure has repeated "
            "at least three times and the same approved "
            "local fallback has already recovered it at "
            "least twice."
        )

        return decision

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
