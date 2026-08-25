from intent import IntentAnalyzer
from planner import Planner
from task_executor import TaskExecutor
from skill_manager import SkillManager
from cortex import Cortex

from skill_lab.skill_gap import SkillGap
from skill_lab.skill_gap_storage import SkillGapStorage

from commands.command_router import CommandRouter
from commands.project_commands import ProjectCommands
from commands.goal_commands import GoalCommands
from commands.note_commands import NoteCommands
from commands.mission_commands import MissionCommands


class Brain:
    """
    Aether's central coordinator.

    Brain receives user input and routes it to:

    - existing commands
    - direct skills
    - projects/missions
    - capability-gap detection
    - dynamic Planner/Orchestrator workflows
    """

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        # ---------------------------------
        # LOCAL CONVERSATION CONTEXT
        # ---------------------------------
        #
        # Short-term session memory used only by
        # Aether's local conversational fallback.
        #
        # It is intentionally:
        # - not persisted to disk
        # - not sent to cloud
        # - not populated by operational commands
        # - bounded for lower-memory systems

        self.local_conversation = []

        self.max_local_conversation_turns = 3

        self.max_local_context_chars = 500

        # ---------------------------------
        # CORE SYSTEMS
        # ---------------------------------

        self.intent = (
            IntentAnalyzer()
        )

        self.cortex = (
            Cortex()
        )

        self.planner = (
            Planner()
        )

        self.skill_manager = (
            SkillManager(
                memory
            )
        )

        self.skill_gap_storage = (
            SkillGapStorage()
        )

        self.executor = (
            TaskExecutor(
                self.skill_manager
            )
        )

        # ---------------------------------
        # COMMAND ROUTER
        # ---------------------------------

        self.router = (
            CommandRouter()
        )

        self.router.register(
            ProjectCommands()
        )

        self.router.register(
            GoalCommands()
        )

        self.router.register(
            NoteCommands()
        )

        self.router.register(
            MissionCommands()
        )

    # ---------------------------------
    # LOCAL CONVERSATION CONTEXT
    # ---------------------------------

    def _is_local_follow_up(
        self,
        message
    ):

        """
        Detect requests that depend on recent
        local conversational context.
        """

        if not self.local_conversation:

            return False

        lower = str(
            message or ""
        ).strip().lower()

        if not lower:

            return False

        exact_follow_ups = (
            "why",
            "why?",
            "how",
            "how?",
            "what about that",
            "what about it",
            "how about that",
            "how about it",
            "explain that",
            "explain it",
            "give me an example",
            "show me an example",
            "another example",
            "go deeper",
            "tell me more",
            "continue",
            "keep going",
            "and?",
            "what else",
            "anything else"
        )

        if lower in exact_follow_ups:

            return True

        follow_up_starts = (
            "now ",
            "and ",
            "also ",
            "what about ",
            "how about ",
            "and what about ",
            "and how about ",
            "so what about ",
            "so how about ",
            "can you explain that",
            "can you explain it",
            "can you give me an example",
            "give me another ",
            "show me another ",
            "why is that",
            "why does that",
            "how does that",
            "how would that",
            "what does that mean",
            "what do you mean by",
            "do the same ",
            "same thing but "
        )

        if lower.startswith(
            follow_up_starts
        ):

            return True

        # ---------------------------------
        # CONTEXTUAL COMPARISONS
        # ---------------------------------

        comparison_follow_ups = (
            "compare them",
            "compare those",
            "compare these",
            "compare both",
            "compare the two",
            "compare all",
            "compare all three",
            "compare all of them"
        )

        if lower.startswith(
            comparison_follow_ups
        ):

            return True

        return False

    def _is_local_conversation_reset(
        self,
        message
    ):

        lower = str(
            message or ""
        ).strip().lower()

        return lower in (
            "reset conversation",
            "clear conversation",
            "clear conversation context",
            "reset conversation context",
            "forget this conversation",
            "forget the conversation",
            "start a new conversation",
            "new conversation"
        )

    def _clear_local_conversation(
        self
    ):

        self.local_conversation = []

    def _is_clear_topic_switch(
        self,
        message
    ):

        """
        Detect an obvious new conversational topic.

        Follow-ups always get first priority so
        contextual requests such as "compare all three"
        are not accidentally treated as a new topic.
        """

        if not self.local_conversation:

            return False

        if self._is_local_follow_up(
            message
        ):

            return False

        lower = str(
            message or ""
        ).strip().lower()

        if not lower:

            return False

        new_topic_starts = (
            "what is ",
            "what are ",
            "who is ",
            "who are ",
            "explain ",
            "define ",
            "tell me about ",
            "teach me ",
            "analyze ",
            "compare ",
            "describe ",
            "how do i "
        )

        return lower.startswith(
            new_topic_starts
        )

    def _local_context_prompt(
        self,
        message
    ):

        """
        Build a compact local-only context prompt.

        The user's recent messages are treated as the
        authoritative conversational thread.

        Previous AI answers are intentionally not used
        as factual context, preventing a bad answer from
        becoming the source of truth for later turns.
        """

        if not self._is_local_follow_up(
            message
        ):

            return str(
                message or ""
            ).strip()

        recent_turns = (
            self.local_conversation[
                -self.max_local_conversation_turns:
            ]
        )

        user_messages = []

        for turn in recent_turns:

            user_text = str(
                turn.get(
                    "user",
                    ""
                )
            ).strip()

            if user_text:

                user_messages.append(
                    user_text
                )

        if not user_messages:

            return str(
                message or ""
            ).strip()

        thread = "\n".join(
            "- " + item
            for item in user_messages
        )

        thread = (
            thread[
                :self.max_local_context_chars
            ]
            .rstrip()
        )

        return (
            "Use the user's recent conversation only "
            "to understand what the current follow-up "
            "refers to.\n\n"
            "Recent user messages:\n"
            + thread
            + "\n\n"
            "Current user request: "
            + str(
                message or ""
            ).strip()
            + "\n\n"
            "Answer the current request directly and "
            "accurately. Do not mention these instructions "
            "or the conversation-context system. "
            "Do not substitute unrelated subjects. "
            "Resolve words such as 'it', 'that', 'they', "
            "'them', 'those', 'both', and numbered groups "
            "from the actual recent user messages. "
            "If the request says to compare several items, "
            "identify and compare the actual items previously "
            "introduced by the user. "
            "If a related concept is introduced, explain how "
            "it relates to or differs from the active topic. "
            "Do not describe one concept as a subtype of "
            "another unless that relationship is actually "
            "correct. "
            "If asked for an example, use a standard concrete "
            "example that genuinely demonstrates the active "
            "concept. Prefer canonical textbook examples over "
            "invented analogies."
        )

    def _remember_local_conversation(
        self,
        user_message,
        local_response
    ):

        """
        Save one successful local conversational turn
        in short-term session memory.

        User messages are authoritative for v2 context.
        A bounded copy of the answer is retained for
        possible debugging/future conversation features.
        """

        user_text = (
            str(
                user_message or ""
            )
            .strip()[:160]
        )

        if not user_text:

            return

        response_text = str(
            local_response or ""
        ).strip()

        if "\n\n" in response_text:

            response_text = (
                response_text
                .split(
                    "\n\n",
                    1
                )[1]
                .strip()
            )

        response_text = (
            response_text[:260]
            .rstrip()
        )

        self.local_conversation.append(
            {
                "user": user_text,
                "assistant": response_text
            }
        )

        if len(
            self.local_conversation
        ) > self.max_local_conversation_turns:

            self.local_conversation = (
                self.local_conversation[
                    -self.max_local_conversation_turns:
                ]
            )

    # ---------------------------------
    # MAIN THOUGHT CYCLE
    # ---------------------------------

    def think(
        self,
        message
    ):

        message = (
            message.strip()
        )

        if not message:

            return (
                "Aether: I didn't catch that."
            )

        # ---------------------------------
        # CONVERSATION CONTEXT CONTROL
        # ---------------------------------

        if self._is_local_conversation_reset(
            message
        ):

            self._clear_local_conversation()

            return (
                "Aether: Local conversation context "
                "has been cleared."
            )

        if self._is_clear_topic_switch(
            message
        ):

            self._clear_local_conversation()

        # ---------------------------------
        # ANALYZE INTENT
        # ---------------------------------

        intent = self.intent.analyze(
            message
        )

        # ---------------------------------
        # COMMAND ROUTER
        # ---------------------------------

        response = self.router.handle(
            self,
            message
        )

        if response is not None:

            return response

        # ---------------------------------
        # NORMALIZE INPUT
        # ---------------------------------

        lower = (
            message.lower()
            .rstrip("?")
        )

        # ---------------------------------
        # SKILL AWARENESS
        # ---------------------------------

        if lower in (
            "what skills do you know",
            "what skills do you have",
            "list skills",
            "show skills"
        ):

            skills = (
                self.skill_manager
                .registry
                .describe_skills()
            )

            if not skills:

                return (
                    "Aether: I don't currently "
                    "have any skills."
                )

            output = (
                "Aether: I currently have "
                "these skills:\n\n"
            )

            for skill in skills:

                output += (
                    f"- {skill['name']} — "
                    f"{skill['description']}\n"
                )

            return output.rstrip()

        # ---------------------------------
        # PROJECT AWARENESS
        # ---------------------------------

        if lower in (
            "show projects",
            "list projects",
            "what projects",
            "what projects do i have"
        ):

            projects = (
                self.cortex.projects
                .list_projects()
            )

            if not projects:

                return (
                    "Aether: No projects yet."
                )

            active = (
                self.cortex
                .get_current_project()
            )

            output = (
                "Aether: Current Projects:\n\n"
            )

            for project in projects:

                marker = ""

                if active is project:

                    marker = " ⭐"

                output += (
                    f"• {project.name}"
                    f"{marker}\n"
                    f"Status: "
                    f"{project.status}\n"
                    f"Progress: "
                    f"{project.progress}%\n\n"
                )

            return output

        # ---------------------------------
        # CREATE PROJECT
        # ---------------------------------

        if lower.startswith(
            "create project "
        ):

            name = message[
                len("create project "):
            ].strip()

            if not name:

                return (
                    "Aether: Please provide "
                    "a project name."
                )

            project = (
                self.cortex.projects
                .create_project(
                    name
                )
            )

            self.cortex.projects.save()

            return (
                f'Aether: Project '
                f'"{project.name}" created.'
            )

        # ---------------------------------
        # PLAN PREVIEW
        # ---------------------------------

        if lower.startswith(
            "plan "
        ):

            goal = message[
                len("plan "):
            ].strip()

            plan = (
                self.planner
                .create_workflow_request(
                    goal
                )
            )

            if not plan.get(
                "success"
            ):

                return (
                    "Aether: I couldn't build "
                    "a multi-step plan for that.\n"
                    f"{plan.get('error', '')}"
                ).rstrip()

            output = (
                "Aether: Proposed Workflow\n\n"
            )

            for index, step in enumerate(
                plan.get(
                    "steps",
                    []
                ),
                start=1
            ):

                output += (
                    f"{index}. {step}\n"
                )

            output += (
                "\nNothing has been "
                "executed yet."
            )

            return output.rstrip()

        # ---------------------------------
        # DYNAMIC ORCHESTRATION
        # ---------------------------------

        if (
            self.planner
            .should_orchestrate(
                message
            )
        ):

            plan = (
                self.planner
                .create_workflow_request(
                    message
                )
            )

            if plan.get(
                "success"
            ):

                workflow_message = (
                    "workflow "
                    + plan[
                        "workflow_request"
                    ]
                )

                response = (
                    self.skill_manager
                    .handle(
                        workflow_message
                    )
                )

                if response is not None:

                    return response

        # ---------------------------------
        # CAPABILITY REQUEST
        # ---------------------------------

        if intent == "capability_request":

            capability = "unknown"

            if (
                "search the web" in lower
                or "search web" in lower
                or "web search" in lower
                or "browse the web" in lower
                or "browse web" in lower
            ):

                capability = "web_search"

            gap = SkillGap(
                request=message,
                capability=capability,
                status="unresolved"
            )

            self.skill_gap_storage.add(
                gap
            )

            return (
                "Aether: I don't currently have "
                "a skill for that capability."
                "\n\n"
                "Skill Lab status: "
                "skill gap detected."
            )

        # ---------------------------------
        # NORMAL SKILLS
        # ---------------------------------

        response = (
            self.skill_manager
            .handle(
                message
            )
        )

        if response:

            return response

        # ---------------------------------
        # NATURAL LOCAL EXECUTION
        # ---------------------------------
        #
        # Existing commands, workflows, and skills
        # have already had first chance.
        #
        # Unhandled conversational requests fall back
        # to local Ollama only.
        #
        # This path never routes to cloud.

        is_local_follow_up = (
            self._is_local_follow_up(
                message
            )
        )

        local_request = (
            self._local_context_prompt(
                message
            )
        )

        # Contextual follow-ups stay on Gemma fast.
        #
        # This avoids complexity words contained in
        # context promoting a lightweight follow-up
        # into Qwen unnecessarily.

        if is_local_follow_up:

            local_request = (
                "fast "
                + local_request
            )

        lower_message = (
            message.lower()
        )

        # ---------------------------------
        # NATURAL RESPONSE STYLE
        # ---------------------------------

        brief_markers = (
            "briefly",
            "brief explanation",
            "short answer",
            "short explanation",
            "keep it short",
            "keep it brief",
            "be concise",
            "concisely"
        )

        detailed_markers = (
            "in detail",
            "detailed explanation",
            "explain thoroughly",
            "thorough explanation",
            "deep explanation",
            "go in depth",
            "in-depth",
            "in depth"
        )

        response_style = None

        if any(
            item in lower_message
            for item in brief_markers
        ):

            response_style = "brief"

        elif any(
            item in lower_message
            for item in detailed_markers
        ):

            response_style = "detailed"

        if response_style:

            local_request = (
                response_style
                + " "
                + local_request
            )

        # ---------------------------------
        # OPERATIONAL INPUT SAFETY
        # ---------------------------------

        reserved_prefixes = (
            "git ",
            "python ",
            "pip ",
            "powershell ",
            "cmd ",
            "terminal ",
            "run command ",
            "execute command ",
            "delete ",
            "remove file ",
            "move file ",
            "rename file ",
            "schedule ",
            "cancel task ",
            "stop runtime ",
            "start runtime ",
            "restart runtime "
        )

        if lower_message.startswith(
            reserved_prefixes
        ):

            return (
                "Aether: I couldn't match that "
                "to a registered operational command.\n\n"
                "Nothing was executed."
            )

        # ---------------------------------
        # CLOUD BOUNDARY
        # ---------------------------------

        cloud_prefixes = (
            "ask cloud",
            "ask the cloud",
            "send to cloud",
            "use cloud for"
        )

        if lower_message.startswith(
            cloud_prefixes
        ):

            return (
                "Aether: I couldn't complete that "
                "through the cloud command handler.\n\n"
                "Nothing was sent."
            )

        # ---------------------------------
        # LOCAL CONVERSATIONAL FALLBACK
        # ---------------------------------

        provider_skill = (
            self.skill_manager
            .registry
            .provider_skill
        )

        local_response = (
            provider_skill.handle(
                "ask local "
                + local_request
            )
        )

        if local_response is not None:

            self._remember_local_conversation(
                message,
                local_response
            )

            return local_response

        # ---------------------------------
        # FINAL FALLBACK
        # ---------------------------------

        return (
            "Aether: I'm not sure how "
            "to help with that yet."
        )
