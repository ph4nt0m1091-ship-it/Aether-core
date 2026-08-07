class Project:
    """
    Represents one long-term project.
    """

    def __init__(self, name):

        self.name = name

        self.goal = ""

        self.status = "Active"

        self.progress = 0

        self.notes = []

        self.tags = []

    def set_goal(self, goal):

        self.goal = goal

    def update_progress(self, progress):

        self.progress = progress

    def add_note(self, note):

        self.notes.append(note)

    def add_tag(self, tag):

        if tag not in self.tags:

            self.tags.append(tag)