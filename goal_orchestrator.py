import re
from datetime import datetime


class GoalOrchestrator:
    """
    Converts higher-level user goals into canonical
    Aether workflow requests.

    The orchestrator plans work only.
    It does not execute commands directly.
    """

    DIRECT_PREFIXES = (
        "workflow ",
        "resume workflow",
        "continue workflow",
        "cancel workflow",
        "workflow status",
        "run ",
        "execute ",
        "terminal ",
        "open ",
        "show ",
        "list ",
        "ask ollama ",
        "calculate ",
        "create project ",
        "set goal "
    )

    FOLLOWUP_WORDS = (
        "summarize",
        "summary",
        "compare",
        "analyze",
        "analyse",
        "evaluate",
        "recommend",
        "best option",
        "best options",
        "save",
        "report",
        "write",
        "open"
    )

    ANALYSIS_WORDS = (
        "compare",
        "analyze",
        "analyse",
        "evaluate",
        "recommend",
        "best option",
        "best options"
    )

    # ---------------------------------
    # SHOULD ORCHESTRATE
    # ---------------------------------

    def should_orchestrate(
        self,
        message
    ):

        message = message.strip()

        if not message:
            return False

        lower = message.lower()

        if lower.startswith(
            self.DIRECT_PREFIXES
        ):
            return False

        # A basic "research X" request should stay
        # with ResearchSkill unless it asks for
        # additional work afterward.
        if lower.startswith(
            "research "
        ):

            return any(
                word in lower
                for word in self.FOLLOWUP_WORDS
            )

        research_phrases = (
            "research ",
            "look into ",
            "find out about ",
            "investigate "
        )

        has_research = any(
            phrase in lower
            for phrase in research_phrases
        )

        has_followup = any(
            word in lower
            for word in self.FOLLOWUP_WORDS
        )

        if has_research and has_followup:
            return True

        has_analysis = any(
            word in lower
            for word in self.ANALYSIS_WORDS
        )

        has_output = any(
            word in lower
            for word in (
                "save",
                "report",
                "write"
            )
        )

        return (
            has_analysis
            and has_output
        )

    # ---------------------------------
    # BUILD PLAN
    # ---------------------------------

    def build(
        self,
        goal
    ):

        goal = goal.strip()

        if not goal:

            return {
                "success": False,
                "error": (
                    "No goal was provided."
                )
            }

        lower = goal.lower()

        steps = []

        research_step_number = None
        analysis_step_number = None

        # ---------------------------------
        # RESEARCH STEP
        # ---------------------------------

        research_topic = (
            self._extract_research_topic(
                goal
            )
        )

        if research_topic:

            steps.append(
                "research "
                + research_topic
            )

            research_step_number = (
                len(steps)
            )

        # ---------------------------------
        # ANALYSIS / SUMMARY STEP
        # ---------------------------------

        wants_compare = (
            "compare" in lower
        )

        wants_analysis = any(
            word in lower
            for word in (
                "analyze",
                "analyse",
                "evaluate",
                "recommend",
                "best option",
                "best options"
            )
        )

        wants_summary = any(
            word in lower
            for word in (
                "summarize",
                "summary",
                "report"
            )
        )

        if research_step_number:

            if (
                wants_compare
                or wants_analysis
            ):

                prompt = (
                    "analyze and compare this research. "
                    "Identify the strongest options, "
                    "important tradeoffs, and give a "
                    "concise recommendation:\n\n"
                    f"{{{{step.{research_step_number}.summary}}}}"
                )

                steps.append(
                    "ask ollama "
                    + prompt
                )

                analysis_step_number = (
                    len(steps)
                )

            elif wants_summary:

                prompt = (
                    "summarize this research in "
                    "three concise bullet points:\n\n"
                    f"{{{{step.{research_step_number}.summary}}}}"
                )

                steps.append(
                    "ask ollama "
                    + prompt
                )

                analysis_step_number = (
                    len(steps)
                )

        # ---------------------------------
        # ANALYSIS WITHOUT RESEARCH
        # ---------------------------------

        elif (
            wants_compare
            or wants_analysis
        ):

            cleaned_goal = (
                self._clean_analysis_goal(
                    goal
                )
            )

            if cleaned_goal:

                steps.append(
                    "ask ollama "
                    + cleaned_goal
                )

                analysis_step_number = (
                    len(steps)
                )

        # ---------------------------------
        # SAVE RESULT
        # ---------------------------------

        if self._wants_save(
            lower
        ):

            filename = (
                self._extract_filename(
                    goal
                )
            )

            if not filename:

                filename = (
                    self._default_report_name()
                )

            reference = None

            if analysis_step_number:

                reference = (
                    f"{{{{step."
                    f"{analysis_step_number}"
                    f".answer}}}}"
                )

            elif research_step_number:

                reference = (
                    f"{{{{step."
                    f"{research_step_number}"
                    f".summary}}}}"
                )

            if reference:

                steps.append(
                    f"save {reference} "
                    f"to {filename}"
                )

        # ---------------------------------
        # OPEN APPLICATION
        # ---------------------------------

        app = self._extract_open_app(
            goal
        )

        if app:

            steps.append(
                "open "
                + app
            )

        # ---------------------------------
        # VALIDATE PLAN
        # ---------------------------------

        if len(steps) < 2:

            return {
                "success": False,
                "error": (
                    "The request does not need "
                    "a multi-step workflow."
                )
            }

        workflow_request = (
            " then ".join(
                steps
            )
        )

        return {
            "success": True,
            "goal": goal,
            "workflow_request": (
                workflow_request
            ),
            "steps": steps,
            "step_count": len(
                steps
            )
        }

    # ---------------------------------
    # EXTRACT RESEARCH TOPIC
    # ---------------------------------

    def _extract_research_topic(
        self,
        goal
    ):

        text = goal.strip()

        starting_patterns = (
            r"^research\s+",
            r"^look\s+into\s+",
            r"^find\s+out\s+about\s+",
            r"^investigate\s+"
        )

        matched = False

        for pattern in starting_patterns:

            if re.match(
                pattern,
                text,
                re.IGNORECASE
            ):

                text = re.sub(
                    pattern,
                    "",
                    text,
                    count=1,
                    flags=re.IGNORECASE
                )

                matched = True
                break

        if not matched:

            lower = goal.lower()

            index = lower.find(
                "research "
            )

            if index == -1:
                return None

            text = goal[
                index
                + len("research "):
            ]

        separators = (
            r",\s*summarize\b",
            r"\s+and\s+summarize\b",
            r",\s*compare\b",
            r"\s+and\s+compare\b",
            r",\s*analyze\b",
            r"\s+and\s+analyze\b",
            r",\s*analyse\b",
            r"\s+and\s+analyse\b",
            r",\s*evaluate\b",
            r"\s+and\s+evaluate\b",
            r",\s*recommend\b",
            r"\s+and\s+recommend\b",
            r",\s*save\b",
            r"\s+and\s+save\b",
            r",\s*write\b",
            r"\s+and\s+write\b",
            r",\s*make\s+me\s+a\s+report\b",
            r"\s+and\s+make\s+me\s+a\s+report\b",
            r",\s*open\b",
            r"\s+and\s+open\b"
        )

        earliest = len(
            text
        )

        for separator in separators:

            match = re.search(
                separator,
                text,
                re.IGNORECASE
            )

            if (
                match
                and match.start()
                < earliest
            ):

                earliest = (
                    match.start()
                )

        topic = text[
            :earliest
        ].strip(
            " ,."
        )

        if not topic:
            return None

        return topic

    # ---------------------------------
    # SAVE HELPERS
    # ---------------------------------

    def _wants_save(
        self,
        lower
    ):

        save_phrases = (
            "save ",
            "save me",
            "save it",
            "save the",
            "make me a report",
            "write a report",
            "write me a report"
        )

        return any(
            phrase in lower
            for phrase in save_phrases
        )

    def _extract_filename(
        self,
        goal
    ):

        patterns = (
            (
                r"\bsave\b.*?\bto\s+"
                r"([^\s,]+?\.(?:txt|md|json))\b"
            ),
            (
                r"\b(?:report|file)\s+"
                r"(?:called|named)\s+"
                r"([^\s,]+?\.(?:txt|md|json))\b"
            )
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                goal,
                re.IGNORECASE
            )

            if match:

                return (
                    match.group(1)
                    .strip()
                    .strip('"')
                )

        return None

    def _default_report_name(
        self
    ):

        timestamp = (
            datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S"
            )
        )

        return (
            "aether_report_"
            + timestamp
            + ".txt"
        )

    # ---------------------------------
    # OPEN APPLICATION
    # ---------------------------------

    def _extract_open_app(
        self,
        goal
    ):

        match = re.search(
            r"\bopen\s+"
            r"(vscode|vs code|notepad|calculator)\b",
            goal,
            re.IGNORECASE
        )

        if not match:
            return None

        app = (
            match.group(1)
            .lower()
        )

        if app == "vs code":
            return "vscode"

        return app

    # ---------------------------------
    # CLEAN ANALYSIS REQUEST
    # ---------------------------------

    def _clean_analysis_goal(
        self,
        goal
    ):

        parts = re.split(
            (
                r"\s+(?:and\s+)?"
                r"(?:save|write|"
                r"make\s+me\s+a\s+report)\b"
            ),
            goal,
            maxsplit=1,
            flags=re.IGNORECASE
        )

        return (
            parts[0]
            .strip(
                " ,."
            )
        )