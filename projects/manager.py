from projects.project import Project
from storage.project_storage import ProjectStorage


class ProjectManager:
    """
    Keeps track of all Aether projects.
    """

    def __init__(self):

        self.projects = {}

        self.storage = ProjectStorage()

        self.storage.restore(self)

    # -----------------------------
    # Create Project
    # -----------------------------

    def create_project(self, name):

        name = name.strip().lower()

        if name not in self.projects:

            project = Project(name)

            project.add_activity(
                "Project created"
            )

            self.projects[name] = project

            self.storage.save(self)

        return self.projects[name]

    # -----------------------------
    # Get Project
    # -----------------------------

    def get_project(self, name):

        return self.projects.get(
            name.strip().lower()
        )

    # -----------------------------
    # Delete Project
    # -----------------------------

    def delete_project(self, name):

        name = name.strip().lower()

        if name in self.projects:

            del self.projects[name]

            self.storage.save(self)

            return True

        return False

    # -----------------------------
    # List Projects
    # -----------------------------

    def list_projects(self):

        return list(
            self.projects.values()
        )

    # -----------------------------
    # Save
    # -----------------------------

    def save(self):

        self.storage.save(self)