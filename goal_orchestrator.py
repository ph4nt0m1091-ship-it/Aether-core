import re
from datetime import datetime


class GoalOrchestrator:
    """
    Converts higher-level natural-language goals into
    canonical Aether workflow requests.

    GoalOrchestrator plans work only.

    It does NOT:
    - execute commands directly
    - bypass permissions
    - modify the computer itself

    Execution remains inside Aether's Workflow Engine.
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
        "set goal ",
        "plan "
    )

    RESEARCH_PHRASES = (
        "research ",
        "look into ",
        "find out about ",
        "investigate "
    )

    SUMMARY_WORDS = (
        "summarize",
        "summary",
        "brief",
        "report"
    )

    ANALYSIS_WORDS = (
        "compare",
        "analyze",
        "analyse",
        "evaluate",
        "recommend",
        "recommendation",
        "best option",
        "best options",
        "pick the best",
        "choose the best",
        "which is better",
        "which one is better"
    )

    SAVE_WORDS = (
        "save ",
        "save it",
        "save me",
        "save the",
        "write a report",
        "write me a report",
        "make me a report",
        "create a report"
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

        # Explicit commands continue through
        # their existing systems.
        if lower.startswith(
            self.DIRECT_PREFIXES
        ):
            return False

        has_research = self._contains_any(
            lower,
            self.RESEARCH_PHRASES
        )

        has_summary = self._contains_any(
            lower,
            self.SUMMARY_WORDS
        )

        has_analysis = self._contains_any(
            lower,
            self.ANALYSIS_WORDS
        )

        has_save = self._contains_any(
            lower,
            self.SAVE_WORDS
        )

        has_open = (
            self._extract_open_app(
                message
            )
            is not None
        )

        # Research plus another requested action
        # should become a workflow.
        if (
            has_research
            and (
                has_summary
                or has_analysis
                or has_save
                or has_open
            )
        ):
            return True

        # Analysis + output/action should also
        # become a workflow.
        if (
            has_analysis
            and (
                has_save
                or has_open
            )
        ):
            return True

        # Summarization + save/open can be planned
        # even when the user did not explicitly
        # use the word "research".
        if (
            has_summary
            and (
                has_save
                or has_open
            )
            and has_research
        ):
            return True

        return False

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
        # DETECT REQUEST TYPE
        # ---------------------------------

        wants_summary = (
            self._contains_any(
                lower,
                self.SUMMARY_WORDS
            )
        )

        wants_analysis = (
            self._contains_any(
                lower,
                self.ANALYSIS_WORDS
            )
        )

        wants_save = (
            self._wants_save(
                lower
            )
        )

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
        # AI ANALYSIS STEP
        # ---------------------------------

        if research_step_number:

            research_reference = (
                f"{{{{step."
                f"{research_step_number}"
                f".summary}}}}"
            )

            if wants_analysis:

                prompt = (
                    "Analyze and compare the following "
                    "research directly. Identify the strongest "
                    "options, important tradeoffs, and give a "
                    "concise recommendation. Do not describe "
                    "your reasoning process.\n\n"
                    + research_reference
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
                    "Summarize the following research "
                    "in three concise bullet points. "
                    "Return only the useful summary.\n\n"
                    + research_reference
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

        elif wants_analysis:

            analysis_goal = (
                self._clean_analysis_goal(
                    goal
                )
            )

            if analysis_goal:

                steps.append(
                    "ask ollama "
                    + (
                        "Answer directly and give a concise "
                        "recommendation when appropriate. "
                        "Do not describe your reasoning process.\n\n"
                        + analysis_goal
                    )
                )

                analysis_step_number = (
                    len(steps)
                )

        # ---------------------------------
        # SAVE STEP
        # ---------------------------------

        if wants_save:

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
        # OPEN APPLICATION STEP
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
                    "The request does not require "
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
    # RESEARCH TOPIC
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

        # Everything after one of these phrases
        # belongs to another workflow action.
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

            r",\s*pick\s+the\s+best\b",
            r"\s+and\s+pick\s+the\s+best\b",

            r",\s*choose\s+the\s+best\b",
            r"\s+and\s+choose\s+the\s+best\b",

            r",\s*save\b",
            r"\s+and\s+save\b",

            r",\s*write\b",
            r"\s+and\s+write\b",

            r",\s*make\s+me\s+a\s+report\b",
            r"\s+and\s+make\s+me\s+a\s+report\b",

            r",\s*create\s+a\s+report\b",
            r"\s+and\s+create\s+a\s+report\b",

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

        return self._contains_any(
            lower,
            self.SAVE_WORDS
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
            ),
            (
                r"\bas\s+"
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
    # CLEAN ANALYSIS GOAL
    # ---------------------------------

    def _clean_analysis_goal(
        self,
        goal
    ):

        text = goal.strip()

        # Remove trailing artifact/app instructions.
        split_patterns = (
            r"\s+and\s+save\b",
            r",\s*save\b",
            r"\s+and\s+write\b",
            r",\s*write\b",
            r"\s+and\s+make\s+me\s+a\s+report\b",
            r",\s*make\s+me\s+a\s+report\b",
            r"\s+and\s+open\b",
            r",\s*open\b"
        )

        earliest = len(
            text
        )

        for pattern in split_patterns:

            match = re.search(
                pattern,
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

        return text[
            :earliest
        ].strip(
            " ,."
        )

    # ---------------------------------
    # UTILITY
    # ---------------------------------

    def _contains_any(
        self,
        text,
        phrases
    ):

        return any(
            phrase in text
            for phrase in phrases
        )