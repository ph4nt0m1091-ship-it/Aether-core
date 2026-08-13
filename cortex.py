from planners.planner_factory import PlannerFactory
from storage.goal_storage import GoalStorage
from projects.manager import ProjectManager
from plan import Plan


class Cortex:
    """
    Aether's executive reasoning system.
    """

    def __init__(self):

        self.current_goal = None
        self.goal_status = "Idle"
        self.progress = 0
        self.plan = None

        self.projects = ProjectManager()
        self.current_project = None

        self.factory = PlannerFactory()
        self.storage = GoalStorage()

    # ---------------------------------
    # RESTORE
    # ---------------------------------

    def restore(self, data):
        """Restore Cortex state from saved data."""

        if data is None:
            return

        self.current_goal = data.get("goal")
        self.goal_status = data.get("status", "Idle")
        self.progress = data.get("progress", 0)

        plan_data = data.get("steps", [])

        if self.current_goal and plan_data:

            self.plan = Plan(self.current_goal)

            for step in plan_data:

                self.plan.add_step(
                    step["description"]
                )

                if step.get("completed", False):

                    self.plan.steps[-1]["completed"] = True

        else:

            self.plan = None

    # ---------------------------------
    # Goals
    # ---------------------------------

    def set_goal(self, goal):

        self.current_goal = goal
        self.goal_status = "Active"

        self.plan = self.factory.create_plan(goal)

        self.progress = self.plan.progress()

        # ---------------------------------
        # Create / get project
        # ---------------------------------

        project = self.projects.create_project(goal)

        project.set_goal(goal)

        project.update_progress(
            self.progress
        )

        # IMPORTANT:
        # Attach Cortex's plan to the project
        # so ProjectStorage can persist it.

        project.set_plan(
            self.plan
        )

        project.add_activity(
            f"Goal set: {goal}"
        )

        self.current_project = project

        self.projects.save()

        self.storage.save(self)

    # ---------------------------------
    # Plan Steps
    # ---------------------------------

    def add_step(self, step):

        if self.plan is None:

            return

        self.plan.add_step(step)

        self.progress = self.plan.progress()

        if self.current_project:

            # Keep project plan synchronized
            self.current_project.set_plan(
                self.plan
            )

            self.current_project.update_progress(
                self.progress
            )

            self.current_project.add_activity(
                f"Plan step added: {step}"
            )

            self.projects.save()

        self.storage.save(self)

    # ---------------------------------
    # Complete Step
    # ---------------------------------

    def complete_step(self, index):

        if self.plan is None:

            return

        self.plan.complete_step(index)

        self.progress = self.plan.progress()

        if self.progress == 100:

            self.goal_status = "Completed"

        if self.current_project:

            # Keep project plan synchronized
            self.current_project.set_plan(
                self.plan
            )

            self.current_project.update_progress(
                self.progress
            )

            self.current_project.add_activity(
                f"Progress updated: {self.progress}%"
            )

            if self.progress == 100:

                self.current_project.status = "Completed"

                self.current_project.add_activity(
                    "Goal completed"
                )

            self.projects.save()

        self.storage.save(self)

    # ---------------------------------
    # Active Workspace
    # ---------------------------------

    def switch_project(self, name):

        project = self.projects.get_project(name)

        if project:

            self.current_project = project

            # ---------------------------------
            # Restore project's plan
            # ---------------------------------

            if project.get_plan() is not None:

                self.plan = project.get_plan()

                self.current_goal = project.goal

                self.progress = project.progress

                self.goal_status = (
                    "Completed"
                    if project.status == "Completed"
                    else "Active"
                )

            else:

                self.plan = None

                self.current_goal = project.goal

                self.progress = project.progress

                self.goal_status = project.status

            project.add_activity(
                "Project activated"
            )

            self.projects.save()

            return True

        return False

    def get_current_project(self):

        return self.current_project

    # ---------------------------------
    # Notes
    # ---------------------------------

    def add_note(self, note):

        if self.current_project is None:

            return False

        self.current_project.add_note(note)

        self.current_project.add_activity(
            f"Note added: {note}"
        )

        self.projects.save()

        return True

    def get_notes(self):

        if self.current_project is None:

            return []

        return self.current_project.get_notes()

    # ---------------------------------
    # Activity
    # ---------------------------------

    def add_activity(self, activity):

        if self.current_project is None:

            return False

        self.current_project.add_activity(
            activity
        )

        self.projects.save()

        return True

    def get_activity(self):

        if self.current_project is None:

            return []

        return self.current_project.get_activity()

    # ---------------------------------
    # Existing Getters
    # ---------------------------------

    def get_goal(self):

        return self.current_goal

    def get_status(self):

        return self.goal_status

    def get_progress(self):

        return self.progress

    def get_plan(self):

        return self.plan