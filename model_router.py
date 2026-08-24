class ModelRouter:
    """
    Chooses the best local model for an Aether task.

    Strategy:
    - gemma3:1b = fast/default conversational brain
    - qwen3:4b = analysis and deeper reasoning
    - qwen3:8b = explicit heavy model only

    Normal requests favor speed.
    More demanding requests earn complexity points.
    """

    FAST_MODEL = "gemma3:1b"
    SMART_MODEL = "qwen3:4b"
    HEAVY_MODEL = "qwen3:8b"

    # Strong signals are enough by themselves
    # to justify the smart model.
    STRONG_COMPLEXITY_SIGNALS = (
        "analyze",
        "analysis",
        "compare",
        "evaluate",
        "diagnose",
        "debug",
        "architecture",
        "tradeoff",
        "tradeoffs",
        "pros and cons",
        "root cause",
        "security review",
        "vulnerability",
        "design a system",
        "design an architecture",
        "strategy"
    )

    # Supporting signals add complexity but do
    # not necessarily require Qwen on their own.
    SUPPORTING_COMPLEXITY_SIGNALS = (
        "explain why",
        "reason",
        "reasoning",
        "weakness",
        "complex",
        "deeply",
        "detailed",
        "figure out",
        "solve",
        "code",
        "programming",
        "step by step",
        "advantages and disadvantages"
    )

    # Kept for compatibility with other Aether
    # components that inspect this attribute.
    COMPLEX_KEYWORDS = (
        STRONG_COMPLEXITY_SIGNALS
        + SUPPORTING_COMPLEXITY_SIGNALS
    )

    def choose(
        self,
        prompt,
        installed_models,
        requested_model=None
    ):

        prompt = str(
            prompt or ""
        )

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

        lower = (
            prompt.lower()
        )

        # ---------------------------------
        # COMPLEXITY SCORE
        # ---------------------------------

        score = 0

        for signal in (
            self.STRONG_COMPLEXITY_SIGNALS
        ):

            if signal in lower:

                score += 2

        for signal in (
            self.SUPPORTING_COMPLEXITY_SIGNALS
        ):

            if signal in lower:

                score += 1

        if len(prompt) > 600:

            score += 1

        if len(prompt) > 1400:

            score += 1

        # ---------------------------------
        # SELECT MODEL
        # ---------------------------------

        if (
            score >= 2
            and self.SMART_MODEL in installed
        ):

            model = (
                self.SMART_MODEL
            )

        elif self.FAST_MODEL in installed:

            model = (
                self.FAST_MODEL
            )

        elif self.SMART_MODEL in installed:

            model = (
                self.SMART_MODEL
            )

        elif installed_models:

            model = (
                installed_models[0]
            )

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
                "prompt": (
                    "Answer naturally and directly. "
                    "Start with the useful answer instead "
                    "of filler such as 'Okay' or "
                    "'Let's break this down'. "
                    "Be concise unless the request asks "
                    "for more detail.\n\n"
                    + prompt
                ),
                "think": False,
                "num_ctx": 2048,
                "num_predict": 140,
                "keep_alive": "30m",
                "tier": "fast"
            }

        # ---------------------------------
        # SMART MODEL
        # ---------------------------------

        if model == self.SMART_MODEL:

            return {
                "success": True,
                "model": model,
                "prompt": (
                    "Give only the final user-facing "
                    "answer. Start immediately with the "
                    "useful content. Do not include "
                    "planning, meta-commentary, or notes "
                    "about how the answer is being "
                    "constructed.\n\n"
                    + prompt
                ),
                "think": False,
                "num_ctx": 2048,
                "num_predict": 200,
                "keep_alive": "30m",
                "tier": "smart"
            }

        # ---------------------------------
        # HEAVY MODEL
        # ---------------------------------

        if model == self.HEAVY_MODEL:

            return {
                "success": True,
                "model": model,
                "prompt": (
                    "Give only the final user-facing "
                    "answer. Do not include planning "
                    "or meta-commentary.\n\n"
                    + prompt
                ),
                "think": False,
                "num_ctx": 2048,
                "num_predict": 240,
                "keep_alive": "30m",
                "tier": "heavy"
            }

        # ---------------------------------
        # UNKNOWN / CUSTOM MODEL
        # ---------------------------------

        return {
            "success": True,
            "model": model,
            "prompt": prompt,
            "think": False,
            "num_ctx": 2048,
            "num_predict": 140,
            "keep_alive": "30m",
            "tier": "custom"
        }
