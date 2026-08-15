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

    Brain receives user input and routes commands
    to the appropriate subsystem.
    """

    def __init__(self, memory):

        self.memory = memory

        # ----------------------------
        # Core Systems
        # ----------------------------

        self.intent = IntentAnalyzer()

        self.cortex = Cortex()

        self.planner = Planner()

        self.skill_manager = SkillManager(
            memory
        )

        self.skill_gap_storage = SkillGapStorage()

        self.executor = TaskExecutor(
            self.skill_manager
        )

        # ----------------------------
        # Command Router
        # ----------------------------

        self.router = CommandRouter()

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

    # ----------------------------
    # Main Thought Cycle
    # ----------------------------

    def think(self, message):

        message = message.strip()

        if not message:

            return (
                "Aether: I didn't catch that."
            )

        # ----------------------------
        # Analyze Intent
        # ----------------------------

        intent = self.intent.analyze(
            message
        )

        # ----------------------------
        # Command Router
        # ----------------------------

        response = self.router.handle(
            self,
            message
        )

        if response is not None:

            return response

        # ----------------------------
        # Normalize Input
        # ----------------------------

        lower = (
            message.lower()
            .rstrip("?")
        )

        # ----------------------------
        # Skill Awareness
        # ----------------------------

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

        # ----------------------------
        # Project Awareness
        # ----------------------------

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

        # ----------------------------
        # Create Project
        # ----------------------------

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
                .create_project(name)
            )

            self.cortex.projects.save()

            return (
                f'Aether: Project '
                f'"{project.name}" created.'
            )

        # ----------------------------
        # Capability Request
        # ----------------------------

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

        # ----------------------------
        # Normal Skills
        # ----------------------------

        response = (
            self.skill_manager
            .handle(message)
        )

        if response:

            return response

        # ----------------------------
        # Unknown Command
        # ----------------------------

        return (
            "Aether: I'm not sure how "
            "to help with that yet."
        )