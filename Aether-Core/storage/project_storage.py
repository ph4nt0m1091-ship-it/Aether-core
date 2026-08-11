import json
import os


class ProjectStorage:
    """
    Saves and restores Aether projects.
    """

    FILE = "storage/projects.json"

    def save(self, project_manager):

        data = []

        for project in project_manager.list_projects():

            data.append({

                "name": project.name,

                "goal": project.goal,

                "status": project.status,

                "progress": project.progress,

                "notes": project.notes,

                "tags": project.tags,

                "activity": project.activity

            })

        os.makedirs("storage", exist_ok=True)

        with open(self.FILE, "w") as file:

            json.dump(
                data,
                file,
                indent=4
            )

    def restore(self, project_manager):

        if not os.path.exists(self.FILE):

            return

        with open(self.FILE, "r") as file:

            data = json.load(file)

        for item in data:

            project = project_manager.create_project(
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