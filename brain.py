from intent import IntentAnalyzer
from planner import Planner
from task_executor import TaskExecutor
from skill_manager import SkillManager
from cortex import Cortex

from commands.command_router import CommandRouter
from commands.project_commands import ProjectCommands


class Brain:
    """
    Aether's central coordinator.
    """

    def __init__(self, memory):

        self.memory = memory

        self.intent = IntentAnalyzer()

        self.skill_manager = SkillManager(memory)

        self.planner = Planner()

        self.executor = TaskExecutor(self.skill_manager)

        self.cortex = Cortex()

        # ----------------------------
        # Command Router
        # ----------------------------

        self.router = CommandRouter()

        self.router.register(ProjectCommands())

    def think(self, message):

        message = message.strip()

        lower = message.lower().rstrip("?")

        intent = self.intent.analyze(message)

        # ---------------------------------
        # Router
        # ---------------------------------

        response = self.router.handle(self, message)

        if response is not None:

            return response

        # ---------------------------------
        # Mission Awareness
        # ---------------------------------

        if lower in (

            "what missions do you know",

            "what missions do you have",

            "list missions",

            "show missions"

        ):

            missions = self.planner.available_missions()

            return (
                "Aether: I currently know these missions:\n\n- "
                + "\n- ".join(missions)
            )

        # ---------------------------------
        # Skill Awareness
        # ---------------------------------

        if lower in (

            "what skills do you know",

            "what skills do you have",

            "list skills",

            "show skills"

        ):

            skills = self.skill_manager.available_skills()

            return (
                "Aether: I currently have these skills:\n\n- "
                + "\n- ".join(skills)
            )

        # ---------------------------------
        # Project Awareness
        # ---------------------------------

        if lower in (

            "show projects",

            "list projects",

            "what projects",

            "what projects do i have"

        ):

            projects = self.cortex.projects.list_projects()

            if not projects:

                return "Aether: No projects yet."

            output = "Aether: Current Projects:\n\n"

            active = self.cortex.get_current_project()

            for project in projects:

                star = ""

                if active is project:

                    star = " ⭐"

                output += (
                    f"• {project.name}{star}\n"
                    f"Status: {project.status}\n"
                    f"Progress: {project.progress}%\n\n"
                )

            return output

        # ---------------------------------
        # Create Project
        # ---------------------------------

        if lower.startswith("create project "):

            name = message[len("create project "):].strip()

            if not name:

                return "Aether: Please provide a project name."

            project = self.cortex.projects.create_project(name)

            self.cortex.projects.save()

            return f'Aether: Project "{project.name}" created.'

        # ---------------------------------
        # Build Goal
        # ---------------------------------

        if lower.startswith("build "):

            goal = message[6:].strip()

            self.cortex.set_goal(goal)

            return "Aether: Goal added to Cortex."

        # ---------------------------------
        # Show Plan
        # ---------------------------------

        if lower == "show plan":

            plan = self.cortex.get_plan()

            if plan is None:

                return "Aether: No active plan."

            output = (
                f"Goal: {self.cortex.get_goal()}\n\n"
                "Plan:\n"
            )

            for i, step in enumerate(plan.steps, start=1):

                mark = "✓" if step["completed"] else "□"

                output += (
                    f"{mark} {i}. "
                    f"{step['description']}\n"
                )

            output += (
                f"\nProgress: "
                f"{self.cortex.get_progress()}%"
            )

            return output

        # ---------------------------------
        # Complete Step
        # ---------------------------------

        if lower.startswith("complete step"):

            try:

                index = int(lower.split()[-1]) - 1

                self.cortex.complete_step(index)

                return "Aether: Step completed."

            except Exception:

                return "Aether: Invalid step."

        # ---------------------------------
        # Mission Execution
        # ---------------------------------

        if intent == "mission":

            task = self.planner.create_task(message)

            if task:

                self.executor.execute(task)

                return "Aether: Mission finished."

        # ---------------------------------
        # Normal Conversation
        # ---------------------------------

        response = self.skill_manager.handle(message)

        if response:

            return response

        return "Aether: I'm not sure how to help with that yet."