from planners.planner_factory import PlannerFactory
from storage.goal_storage import GoalStorage
from projects.manager import ProjectManager


class Cortex:
    """
    Aether's executive reasoning system.
    """

    def __init__(self):

        self.current_goal = None
        self.goal_status = "Idle"
        self.progress = 0
        self.plan = None

        # Workspace
        self.projects = ProjectManager()
        self.current_project = None

        self.factory = PlannerFactory()
        self.storage = GoalStorage()

    # ---------------------------------
    # Goals
    # ---------------------------------

    def set_goal(self, goal):

        self.current_goal = goal
        self.goal_status = "Active"

        self.plan = self.factory.create_plan(goal)

        self.progress = self.plan.progress()

        project = self.projects.create_project(goal)

        project.set_goal(goal)
        project.update_progress(self.progress)

        self.current_project = project

        self.projects.save()

        self.storage.save(self)

    def add_step(self, step):

        if self.plan:

            self.plan.add_step(step)

            self.progress = self.plan.progress()

            if self.current_project:

                self.current_project.update_progress(
                    self.progress
                )

                self.projects.save()

            self.storage.save(self)

    def complete_step(self, index):

        if self.plan:

            self.plan.complete_step(index)

            self.progress = self.plan.progress()

            if self.progress == 100:

                self.goal_status = "Completed"

            if self.current_project:

                self.current_project.update_progress(
                    self.progress
                )

                if self.progress == 100:

                    self.current_project.status = "Completed"

                self.projects.save()

            self.storage.save(self)

    # ---------------------------------
    # Active Workspace
    # ---------------------------------

    def switch_project(self, name):

        project = self.projects.get_project(name)

        if project:

            self.current_project = project
            return True

        return False

    def get_current_project(self):

        return self.current_project

    # ---------------------------------
    # Existing getters
    # ---------------------------------

    def get_goal(self):

        return self.current_goal

    def get_status(self):

        return self.goal_status

    def get_progress(self):

        return self.progress

    def get_plan(self):

        return self.plan