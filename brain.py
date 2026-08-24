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
        #
        # "plan <goal>" lets you inspect what
        # Aether WOULD execute without running it.

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
        #
        # Higher-level requests are converted
        # into canonical WorkflowSkill commands.
        #
        # Planner creates the plan.
        # WorkflowEngine executes it.
        # PermissionManager still controls
        # sensitive terminal/system actions.

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
        # Every existing command, workflow, and skill
        # has already had first chance to handle the
        # request before this point.
        #
        # Unhandled conversational requests fall back
        # to local Ollama only.
        #
        # This path never routes to cloud.

        local_request = (
            message
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

            return local_response

        # ---------------------------------
        # FINAL FALLBACK
        # ---------------------------------

        return (
            "Aether: I'm not sure how "
            "to help with that yet."
        )
