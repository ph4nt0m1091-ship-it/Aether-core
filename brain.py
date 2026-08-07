from cortex import Cortex
from intent import IntentAnalyzer
from planner import Planner
from task_executor import TaskExecutor
from skill_manager import SkillManager


class Brain:
    """
    Aether's central coordinator.
    """

    def __init__(self, memory):

        self.memory = memory

        self.cortex = Cortex()

        self.planner = Planner()

        self.intent = IntentAnalyzer()

        self.skill_manager = SkillManager(memory)

        self.executor = TaskExecutor(self.skill_manager)

    def think(self, message):

        message = message.strip()

        lower = (
            message.lower()
            .replace("?", "")
            .replace(".", "")
            .replace("!", "")
            .replace(",", "")
        )

        intent = self.intent.analyze(message)

        # ----------------------------
        # Cortex Awareness
        # ----------------------------

        if lower in (
            "what is your current goal",
            "what are you working on",
            "current goal",
            "goal",
        ):

            goal = self.cortex.get_goal()

            if goal:

                return (
                    f"Aether:\n\n"
                    f"Current Goal: {goal}\n"
                    f"Status: {self.cortex.get_status()}\n"
                    f"Progress: {self.cortex.get_progress()}%"
                )

            return "Aether: I don't have a current goal."

        # ----------------------------
        # Show Plan
        # ----------------------------

        if lower in (
            "show plan",
            "what is the plan",
            "show my plan",
            "plan",
        ):

            plan = self.cortex.get_plan()

            if not plan:

                return "Aether: I don't have an active plan yet."

            lines = [
                "Aether:",
                "",
                f"Goal: {plan.goal}",
                "",
                "Plan:",
            ]

            for step in plan.list_steps():

                mark = "✓" if step["completed"] else "□"

                lines.append(f"{mark} {step['description']}")

            lines.append("")
            lines.append(
                f"Progress: {plan.progress()}%"
            )

            return "\n".join(lines)

        # Store newest goal
        self.cortex.set_goal(message)

        # ----------------------------
        # Mission awareness
        # ----------------------------

        if lower in (
            "what missions do you have",
            "what missions do you know",
            "list missions",
            "show missions",
        ):

            missions = self.planner.available_missions()

            return (
                "Aether: I currently know these missions:\n\n- "
                + "\n- ".join(missions)
            )

        # ----------------------------
        # Skill awareness
        # ----------------------------

        if lower in (
            "what skills do you have",
            "what skills do you know",
            "list skills",
            "show skills",
        ):

            skills = self.skill_manager.available_skills()

            return (
                "Aether: I currently have these skills:\n\n- "
                + "\n- ".join(skills)
            )

        # ----------------------------
        # Mission execution
        # ----------------------------

        if intent == "mission":

            task = self.planner.create_task(message)

            if task:

                self.executor.execute(task)

                return "Aether: Mission finished."

        # ----------------------------
        # Normal conversation
        # ----------------------------

        response = self.skill_manager.handle(message)

        if response:

            return response

        return "Aether: I'm not sure how to help with that yet."