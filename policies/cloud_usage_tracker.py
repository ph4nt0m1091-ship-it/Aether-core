class CloudUsageTracker:
    """
    Tracks safe cloud usage metadata for the
    current Aether process.

    This tracker intentionally does NOT store:
    - prompts
    - responses
    - API keys
    - credentials
    - local/private data

    Usage is currently session-only and is not
    persisted to disk.
    """

    def __init__(
        self
    ):

        self.reset()

    # ---------------------------------
    # INTEGER
    # ---------------------------------

    def _integer(
        self,
        value
    ):

        try:

            return int(
                value or 0
            )

        except (
            TypeError,
            ValueError
        ):

            return 0

    # ---------------------------------
    # RECORD
    # ---------------------------------

    def record(
        self,
        provider,
        model,
        usage=None,
        success=True
    ):

        usage = (
            usage
            if isinstance(
                usage,
                dict
            )
            else {}
        )

        provider = str(
            provider or "unknown"
        ).strip()

        model = str(
            model or "unknown"
        ).strip()

        prompt_tokens = (
            self._integer(
                usage.get(
                    "prompt_tokens"
                )
            )
        )

        completion_tokens = (
            self._integer(
                usage.get(
                    "completion_tokens"
                )
            )
        )

        total_tokens = (
            self._integer(
                usage.get(
                    "total_tokens"
                )
            )
        )

        if (
            total_tokens <= 0
            and (
                prompt_tokens
                or completion_tokens
            )
        ):

            total_tokens = (
                prompt_tokens
                + completion_tokens
            )

        free_model = (
            model.lower()
            == "openrouter/free"
            or model.lower().endswith(
                ":free"
            )
        )

        self.request_count += 1

        if success:

            self.success_count += 1

        else:

            self.failure_count += 1

        self.prompt_tokens += (
            prompt_tokens
        )

        self.completion_tokens += (
            completion_tokens
        )

        self.total_tokens += (
            total_tokens
        )

        self.last_request = {
            "provider": provider,
            "model": model,
            "free_model": (
                free_model
            ),
            "prompt_tokens": (
                prompt_tokens
            ),
            "completion_tokens": (
                completion_tokens
            ),
            "total_tokens": (
                total_tokens
            ),
            "success": bool(
                success
            )
        }

        return dict(
            self.last_request
        )

    # ---------------------------------
    # LAST
    # ---------------------------------

    def last(
        self
    ):

        if self.last_request is None:

            return None

        return dict(
            self.last_request
        )

    # ---------------------------------
    # STATUS
    # ---------------------------------

    def status(
        self
    ):

        return {
            "request_count": (
                self.request_count
            ),
            "success_count": (
                self.success_count
            ),
            "failure_count": (
                self.failure_count
            ),
            "prompt_tokens": (
                self.prompt_tokens
            ),
            "completion_tokens": (
                self.completion_tokens
            ),
            "total_tokens": (
                self.total_tokens
            ),
            "last_request": (
                self.last()
            )
        }

    # ---------------------------------
    # RESET
    # ---------------------------------

    def reset(
        self
    ):

        self.request_count = 0

        self.success_count = 0

        self.failure_count = 0

        self.prompt_tokens = 0

        self.completion_tokens = 0

        self.total_tokens = 0

        self.last_request = None

        return True