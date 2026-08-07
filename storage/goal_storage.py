import json
import os


class GoalStorage:
    """
    Saves and restores Cortex goals.
    """

    FILE_NAME = "goal.json"

    def save(self, cortex):

        if cortex.get_plan() is None:
            return

        data = {
            "goal": cortex.get_goal(),
            "status": cortex.get_status(),
            "progress": cortex.get_progress(),
            "steps": cortex.get_plan().steps
        }

        with open(self.FILE_NAME, "w") as file:
            json.dump(data, file, indent=4)

    def load(self):

        if not os.path.exists(self.FILE_NAME):
            return None

        with open(self.FILE_NAME, "r") as file:
            return json.load(file)

    def restore(self, cortex):

        data = self.load()

        if data is None:
            return

        cortex.current_goal = data["goal"]
        cortex.goal_status = data["status"]
        cortex.progress = data["progress"]

        cortex.plan = cortex.factory.create_plan(
            cortex.current_goal
        )

        for i, step in enumerate(data["steps"]):

            cortex.plan.steps[i]["completed"] = step["completed"]