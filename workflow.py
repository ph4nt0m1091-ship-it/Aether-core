class Workflow:
    """
    Represents a sequence of actions for Aether.

    Workflows are separate from predefined missions.
    They are intended for dynamic, user-requested work.
    """

    def __init__(self, goal=""):

        self.goal = goal
        self.steps = []
        self.current_step = 0
        self.results = []
        self.status = "pending"

    # ---------------------------------
    # ADD STEP
    # ---------------------------------

    def add_step(
        self,
        step_type,
        action,
        data=None,
        target=None
    ):

        self.steps.append(
            {
                "type": step_type,
                "action": action,
                "data": data or {},
                "target": target
            }
        )

    # ---------------------------------
    # STATE
    # ---------------------------------

    def has_next_step(self):

        return (
            self.current_step
            < len(self.steps)
        )

    def next_step(self):

        if not self.has_next_step():

            return None

        step = self.steps[
            self.current_step
        ]

        self.current_step += 1

        return step

    def add_result(
        self,
        result
    ):

        self.results.append(
            result
        )

    def progress(self):

        total = len(
            self.steps
        )

        if total == 0:

            return 100

        return int(
            (
                self.current_step
                / total
            )
            * 100
        )

    def reset(self):

        self.current_step = 0
        self.results = []
        self.status = "pending"

    def __len__(self):

        return len(
            self.steps
        )