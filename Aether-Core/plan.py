class Plan:
    """
    Represents a multi-step plan.
    """

    def __init__(self, goal):

        self.goal = goal
        self.steps = []

    def add_step(self, step):

        self.steps.append({
            "description": step,
            "completed": False
        })

    def complete_step(self, index):

        if 0 <= index < len(self.steps):
            self.steps[index]["completed"] = True

    def progress(self):

        if not self.steps:
            return 0

        completed = sum(
            step["completed"]
            for step in self.steps
        )

        return int((completed / len(self.steps)) * 100)

    def list_steps(self):

        return self.steps