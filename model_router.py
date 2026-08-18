class ModelRouter:
    """
    Chooses the best local model for an Aether task.

    Strategy:
    - gemma3:1b = fast/default brain
    - qwen3:4b = deeper reasoning
    - qwen3:8b = explicit heavy model only

    The router favors speed unless the request
    appears to require more reasoning.
    """

    FAST_MODEL = "gemma3:1b"

    SMART_MODEL = "qwen3:4b"

    HEAVY_MODEL = "qwen3:8b"

    COMPLEX_KEYWORDS = (
        "analyze",
        "analysis",
        "compare",
        "reason",
        "reasoning",
        "architecture",
        "debug",
        "diagnose",
        "design",
        "security",
        "vulnerability",
        "weakness",
        "strategy",
        "plan",
        "complex",
        "deeply",
        "detailed",
        "evaluate",
        "tradeoff",
        "tradeoffs",
        "pros and cons",
        "explain why",
        "figure out",
        "solve",
        "code",
        "programming"
    )

    def choose(
        self,
        prompt,
        installed_models,
        requested_model=None
    ):

        installed = set(
            installed_models
        )

        # ---------------------------------
        # EXPLICIT MODEL
        # ---------------------------------

        if requested_model:

            if requested_model in installed:

                return self._config_for(
                    requested_model,
                    prompt
                )

            return {
                "success": False,
                "error": (
                    f'Model "{requested_model}" '
                    "is not installed."
                )
            }

        lower = prompt.lower()

        # ---------------------------------
        # COMPLEXITY SCORE
        # ---------------------------------

        score = 0

        for keyword in self.COMPLEX_KEYWORDS:

            if keyword in lower:

                score += 1

        if len(prompt) > 500:

            score += 1

        if len(prompt) > 1500:

            score += 2

        # ---------------------------------
        # SELECT MODEL
        # ---------------------------------

        if (
            score >= 2
            and self.SMART_MODEL in installed
        ):

            model = self.SMART_MODEL

        elif self.FAST_MODEL in installed:

            model = self.FAST_MODEL

        elif self.SMART_MODEL in installed:

            model = self.SMART_MODEL

        elif installed_models:

            model = installed_models[0]

        else:

            return {
                "success": False,
                "error": (
                    "No Ollama models are installed."
                )
            }

        return self._config_for(
            model,
            prompt
        )

    # ---------------------------------
    # MODEL CONFIG
    # ---------------------------------

    def _config_for(
        self,
        model,
        prompt
    ):

        # ---------------------------------
        # FAST MODEL
        # ---------------------------------

        if model == self.FAST_MODEL:

            return {
                "success": True,
                "model": model,
                "prompt": prompt,
                "think": False,
                "num_ctx": 2048,
                "num_predict": 120,
                "keep_alive": "30m",
                "tier": "fast"
            }

        # ---------------------------------
        # SMART QWEN
        # ---------------------------------

        if model == self.SMART_MODEL:

            return {
                "success": True,
                "model": model,
                "prompt": (
                    "Answer the request directly. "
                    "Do not describe your reasoning process, "
                    "do not restate the request, and do not "
                    "talk about how you are answering.\n\n"
                    + prompt
                ),
                "think": False,
                "num_ctx": 2048,
                "num_predict": 180,
                "keep_alive": "30m",
                "tier": "smart"
            }

        # ---------------------------------
        # HEAVY QWEN
        # ---------------------------------

        if model == self.HEAVY_MODEL:

            return {
                "success": True,
                "model": model,
                "prompt": (
                    "/no_think\n"
                    + prompt
                ),
                "think": False,
                "num_ctx": 2048,
                "num_predict": 220,
                "keep_alive": "30m",
                "tier": "heavy"
            }

        # ---------------------------------
        # UNKNOWN MODEL
        # ---------------------------------

        return {
            "success": True,
            "model": model,
            "prompt": prompt,
            "think": False,
            "num_ctx": 2048,
            "num_predict": 120,
            "keep_alive": "30m",
            "tier": "custom"
        }