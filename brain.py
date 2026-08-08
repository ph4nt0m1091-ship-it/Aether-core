from intent import IntentAnalyzer
from planner import Planner
from task_executor import TaskExecutor
from skill_manager import SkillManager
from cortex import Cortex

from commands.command_router import CommandRouter
from commands.project_commands import ProjectCommands
from commands.goal_commands import GoalCommands
from commands.note_commands import NoteCommands


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

        self.skill_manager = SkillManager(memory)

        self.executor = TaskExecutor(self.skill_manager)

        # ----------------------------
        # Command Router
        # ----------------------------

        self.router = CommandRouter()

        self.router.register(ProjectCommands())
        self.router.register(GoalCommands())
        self.router.register(NoteCommands())

    # ----------------------------
    # Main Thought Cycle
    # ----------------------------

    def think(self, message):

        message = message.strip()

        if not message:

            return "Aether: I didn't catch that."

        # ----------------------------
        # Command Router
        # ----------------------------

        response = self.router.handle(self, message)

        if response is not None:

            return response

        # ----------------------------
        # Normalize Input
        # ----------------------------

        lower = message.lower().rstrip("?")

        # ----------------------------
        # Mission Awareness
        # ----------------------------

        if lower in (
            "what missions do you know",
            "what missions do you have",
            "list missions",
            "show missions"
        ):

            missions = self.planner.available_missions()

            if not missions:

                return (
                    "Aether: I don't currently have any missions."
                )

            return (
                "Aether: I currently know these missions:\n\n- "
                + "\n- ".join(missions)
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

            skills = self.skill_manager.available_skills()

            if not skills:

                return (
                    "Aether: I don't currently have any skills."
                )

            return (
                "Aether: I currently have these skills:\n\n- "
                + "\n- ".join(skills)
            )

        # ----------------------------
        # Project Awareness
        # ----------------------------

        if lower in (
            "show projects",
            "list projects",
            "what projects",
            "what projects do i have"
        ):

            projects = self.cortex.projects.list_projects()

            if not projects:

                return "Aether: No projects yet."

            active = self.cortex.get_current_project()

            output = "Aether: Current Projects:\n\n"

            for project in projects:

                marker = ""

                if active is project:

                    marker = " ⭐"

                output += (
                    f"• {project.name}{marker}\n"
                    f"Status: {project.status}\n"
                    f"Progress: {project.progress}%\n\n"
                )

            return output

        # ----------------------------
        # Create Project
        # ----------------------------

        if lower.startswith("create project "):

            name = message[len("create project "):].strip()

            if not name:

                return (
                    "Aether: Please provide a project name."
                )

            project = self.cortex.projects.create_project(name)

            self.cortex.projects.save()

            return (
                f'Aether: Project "{project.name}" created.'
            )

        # ----------------------------
        # Mission Execution
        # ----------------------------

        intent = self.intent.analyze(message)

        if intent == "mission":

            task = self.planner.create_task(message)

            if task:

                self.executor.execute(task)

                return "Aether: Mission finished."

        # ----------------------------
        # Skills / Normal Conversation
        # ----------------------------

        response = self.skill_manager.handle(message)

        if response:

            return response

        # ----------------------------
        # Unknown Command
        # ----------------------------

        return (
            "Aether: I'm not sure how to help with that yet."
        )