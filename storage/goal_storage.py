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
        """Restore Cortex state from storage."""
        data = self.load()
        if data is None:
            return

        # Let the Cortex object restore itself from the data
        cortex.restore(data)