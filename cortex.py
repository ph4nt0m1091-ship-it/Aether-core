from planners.planner_factory import PlannerFactory
from storage.goal_storage import GoalStorage
from projects.manager import ProjectManager
from plan import Plan


class Cortex:
    """
    Aether's executive reasoning system.

    Cortex manages:
    - Goals
    - Plans
    - Progress
    - Current project
    - Project workspace state
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
        """
        Restore Cortex state from saved goal data.
        """

        if data is None:
            return

        self.current_goal = data.get(
            "goal"
        )

        self.goal_status = data.get(
            "status",
            "Idle"
        )

        self.progress = data.get(
            "progress",
            0
        )

        plan_data = data.get(
            "steps",
            []
        )

        if self.current_goal and plan_data:

            self.plan = Plan(
                self.current_goal
            )

            for step in plan_data:

                self.plan.add_step(
                    step.get(
                        "description",
                        ""
                    )
                )

                self.plan.steps[-1]["completed"] = (
                    step.get(
                        "completed",
                        False
                    )
                )

        else:

            self.plan = None

        # ---------------------------------
        # Reconnect restored plan to project
        # ---------------------------------

        if self.current_goal:

            project = self.projects.get_project(
                self.current_goal
            )

            if project is not None:

                self.current_project = project

                project.set_goal(
                    self.current_goal
                )

                project.set_plan(
                    self.plan
                )

                project.update_progress(
                    self.progress
                )

    # ---------------------------------
    # Goals
    # ---------------------------------

    def set_goal(self, goal):
        """
        Create a goal and attach its plan
        directly to the current project.
        """

        goal = goal.strip()

        if not goal:

            return False

        self.current_goal = goal
        self.goal_status = "Active"

        self.plan = self.factory.create_plan(
            goal
        )

        self.progress = self.plan.progress()

        project = self.projects.create_project(
            goal
        )

        project.set_goal(
            goal
        )

        project.set_plan(
            self.plan
        )

        project.update_progress(
            self.progress
        )

        project.add_activity(
            f"Goal set: {goal}"
        )

        project.add_activity(
            "Project plan created"
        )

        self.current_project = project

        self.projects.save()

        self.storage.save(
            self
        )

        return True

    # ---------------------------------
    # Add Step
    # ---------------------------------

    def add_step(self, step):

        if self.plan is None:

            return False

        self.plan.add_step(
            step
        )

        self.progress = self.plan.progress()

        if self.current_project:

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

        self.storage.save(
            self
        )

        return True

    # ---------------------------------
    # Complete Step
    # ---------------------------------

    def complete_step(self, index):
        """
        Complete one plan step.

        Returns:
            True  = successful
            False = no plan or invalid step
        """

        if self.plan is None:

            return False

        if index < 0:

            return False

        if index >= len(
            self.plan.steps
        ):

            return False

        self.plan.complete_step(
            index
        )

        self.progress = self.plan.progress()

        if self.progress == 100:

            self.goal_status = "Completed"

        if self.current_project:

            self.current_project.set_plan(
                self.plan
            )

            self.current_project.update_progress(
                self.progress
            )

            self.current_project.add_activity(
                f"Plan step completed: {index + 1}"
            )

            if self.progress == 100:

                self.current_project.status = (
                    "Completed"
                )

                self.current_project.add_activity(
                    "Goal completed"
                )

            self.projects.save()

        self.storage.save(
            self
        )

        return True

    # ---------------------------------
    # Active Workspace
    # ---------------------------------

    def switch_project(self, name):
        """
        Switch to an existing project.

        Reconnect Cortex to the project's
        saved goal and plan.
        """

        project = self.projects.get_project(
            name
        )

        if project is None:

            return False

        self.current_project = project

        self.current_goal = project.goal

        self.plan = project.get_plan()

        self.progress = project.progress

        if project.status == "Completed":

            self.goal_status = "Completed"

        elif project.goal:

            self.goal_status = "Active"

        else:

            self.goal_status = "Idle"

        project.add_activity(
            "Project activated"
        )

        self.projects.save()

        return True

    # ---------------------------------
    # Current Project
    # ---------------------------------

    def get_current_project(self):

        return self.current_project

    # ---------------------------------
    # Notes
    # ---------------------------------

    def add_note(self, note):

        if self.current_project is None:

            return False

        self.current_project.add_note(
            note
        )

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
    # Getters
    # ---------------------------------

    def get_goal(self):

        return self.current_goal

    def get_status(self):

        return self.goal_status

    def get_progress(self):

        return self.progress

    def get_plan(self):

        return self.plan