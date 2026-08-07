from intent import IntentAnalyzer
from planner import Planner
from task_executor import TaskExecutor
from skill_manager import SkillManager
from cortex import Cortex


class Brain:
    """
    Aether's central coordinator.
    """

    def __init__(self, memory):

        self.memory = memory

        self.intent = IntentAnalyzer()

        self.planner = Planner()

        self.cortex = Cortex()

        self.skill_manager = SkillManager(memory)

        self.executor = TaskExecutor(self.skill_manager)

    def think(self, message):

        message = message.strip()

        lower = message.lower()

        intent = self.intent.analyze(message)

        # ----------------------------
        # Mission awareness
        # ----------------------------

        if lower.rstrip("?") in (
            "what missions do you have",
            "what missions do you know",
            "list missions",
            "show missions"
        ):

            missions = self.planner.available_missions()

            return (
                "Aether: I currently know these missions:\n\n- "
                + "\n- ".join(missions)
            )

        # ----------------------------
        # Skill awareness
        # ----------------------------

        if lower.rstrip("?") in (
            "what skills do you have",
            "what skills do you know",
            "list skills",
            "show skills"
        ):

            skills = self.skill_manager.available_skills()

            return (
                "Aether: I currently have these skills:\n\n- "
                + "\n- ".join(skills)
            )

        # ----------------------------
        # Show Plan
        # ----------------------------

        if intent == "show_plan":

            plan = self.cortex.get_plan()

            if not plan:

                return "Aether: No active goal."

            output = f"\nGoal: {self.cortex.get_goal()}\n\n"
            output += "Plan:\n"

            for i, step in enumerate(plan.steps):

                mark = "✓" if step["completed"] else "□"

                output += f"{mark} {i + 1}. {step['description']}\n"

            output += f"\nProgress: {self.cortex.get_progress()}%"

            return output

        # ----------------------------
        # Complete Step
        # ----------------------------

        if intent == "complete_step":

            try:

                number = int(
                    lower.replace("complete step", "").strip()
                )

                self.cortex.complete_step(number - 1)

                return "Aether: Step completed."

            except ValueError:

                return "Aether: Please specify a valid step number."

        # ----------------------------
        # Mission execution
        # ----------------------------

        if intent == "mission":

            self.cortex.set_goal(message)

            task = self.planner.create_task(message)

            if task:

                self.executor.execute(task)

                return "Aether: Mission finished."

            return "Aether: Goal added to Cortex."

        # ----------------------------
        # Conversation
        # ----------------------------

        response = self.skill_manager.handle(message)

        if response:

            return response

        return "Aether: I'm not sure how to help with that yet."