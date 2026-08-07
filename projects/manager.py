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

    def create_project(self, name):

        name = name.strip().lower()

        if name not in self.projects:

            self.projects[name] = Project(name)

            self.storage.save(self)

        return self.projects[name]

    def get_project(self, name):

        return self.projects.get(name.strip().lower())

    def delete_project(self, name):

        name = name.strip().lower()

        if name in self.projects:

            del self.projects[name]

            self.storage.save()

            return True

        return False

    def list_projects(self):

        return list(self.projects.values())

    def save(self):

        self.storage.save(self)