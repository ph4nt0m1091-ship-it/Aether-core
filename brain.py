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

        self.planner = Planner()

        self.intent = IntentAnalyzer()

        self.skill_manager = SkillManager(memory)

        self.executor = TaskExecutor(self.skill_manager)

    def think(self, message):

        message = message.strip()

        lower = message.lower()

        intent = self.intent.analyze(message)

        # ----------------------------
        # Mission awareness
        # ----------------------------

        if lower in (
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

        if lower in (
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