import json
import os

from plan import Plan


class ProjectStorage:
    """
    Saves and restores Aether projects.
    """

    FILE = "storage/projects.json"

    # -----------------------------
    # Save
    # -----------------------------

    def save(self, project_manager):

        data = []

        for project in project_manager.list_projects():

            project_data = {

                "name": project.name,

                "goal": project.goal,

                "status": project.status,

                "progress": project.progress,

                "notes": project.notes,

                "tags": project.tags,

                "activity": project.activity,

                "plan": None
            }

            # -----------------------------
            # Save Project Plan
            # -----------------------------

            if project.get_plan() is not None:

                project_data["plan"] = {
                    "goal": project.get_plan().goal,
                    "steps": project.get_plan().steps
                }

            data.append(project_data)

        os.makedirs("storage", exist_ok=True)

        with open(self.FILE, "w") as file:

            json.dump(
                data,
                file,
                indent=4
            )

    # -----------------------------
    # Restore
    # -----------------------------

    def restore(self, project_manager):

        if not os.path.exists(self.FILE):

            return

        with open(self.FILE, "r") as file:

            data = json.load(file)

        for item in data:

            project = project_manager.restore_project(
                item["name"]
            )

            project.goal = item.get(
                "goal",
                ""
            )

            project.status = item.get(
                "status",
                "Active"
            )

            project.progress = item.get(
                "progress",
                0
            )

            project.notes = item.get(
                "notes",
                []
            )

            project.tags = item.get(
                "tags",
                []
            )

            # -----------------------------
            # Restore Project Plan
            # -----------------------------

            plan_data = item.get(
                "plan"
            )

            if plan_data:

                plan = Plan(
                    plan_data.get(
                        "goal",
                        project.goal
                    )
                )

                for step in plan_data.get(
                    "steps",
                    []
                ):

                    plan.add_step(
                        step.get(
                            "description",
                            ""
                        )
                    )

                    plan.steps[-1]["completed"] = step.get(
                        "completed",
                        False
                    )

                project.set_plan(plan)

            else:

                project.set_plan(None)

            # -----------------------------
            # Activity Compatibility
            # -----------------------------

            activity = item.get(
                "activity",
                []
            )

            restored_activity = []

            for event in activity:

                # New timestamped event
                if isinstance(event, dict):

                    restored_activity.append(event)

                # Old string event
                else:

                    restored_activity.append({
                        "timestamp": "Unknown",
                        "message": str(event)
                    })

            project.activity = restored_activity