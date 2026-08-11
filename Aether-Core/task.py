class Task:
    """
    Represents a mission that Aether needs to complete.
    """

    def __init__(self, goal):

        self.goal = goal
        self.steps = []
        self.current_step = 0

    def add_step(self, skill, action, **data):

        step = {
            "skill": skill,
            "action": action,
            "data": data
        }

        self.steps.append(step)

    def has_next_step(self):

        return self.current_step < len(self.steps)

    def next_step(self):

        if not self.has_next_step():
            return None

        step = self.steps[self.current_step]
        self.current_step += 1

        return step

    def reset(self):

        self.current_step = 0

    def __len__(self):

        return len(self.steps)