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

        self.skill_manager = SkillManager(memory)

        self.executor = TaskExecutor(self.skill_manager)

    def think(self, message):

        message = message.strip()

        # Ask the planner if this is a mission
        task = self.planner.create_task(message)

        if task:

            self.executor.execute(task)

            return "Aether: Mission finished."

        # Normal conversation
        response = self.skill_manager.handle(message)

        if response:

            return response

        return "Aether: I'm not sure how to help with that yet."