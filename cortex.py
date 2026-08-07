from planners.planner_factory import PlannerFactory


class Cortex:
    """
    Aether's executive reasoning system.
    """

    def __init__(self):

        self.current_goal = None
        self.goal_status = "Idle"
        self.progress = 0
        self.plan = None

        self.factory = PlannerFactory()

    def set_goal(self, goal):

        self.current_goal = goal
        self.goal_status = "Active"

        self.plan = self.factory.create_plan(goal)

        self.progress = self.plan.progress()

    def add_step(self, step):

        if self.plan:

            self.plan.add_step(step)

            self.progress = self.plan.progress()

    def complete_step(self, index):

        if self.plan:

            self.plan.complete_step(index)

            self.progress = self.plan.progress()

            if self.progress == 100:

                self.goal_status = "Completed"

    def get_goal(self):

        return self.current_goal

    def get_status(self):

        return self.goal_status

    def get_progress(self):

        return self.progress

    def get_plan(self):

        return self.plan