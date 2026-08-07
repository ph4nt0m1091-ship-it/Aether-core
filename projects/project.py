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

    # -----------------------------
    # Goal
    # -----------------------------

    def set_goal(self, goal):

        self.goal = goal

    # -----------------------------
    # Progress
    # -----------------------------

    def update_progress(self, progress):

        self.progress = progress

    # -----------------------------
    # Notes
    # -----------------------------

    def add_note(self, note):

        note = note.strip()

        if note:

            self.notes.append(note)

    def get_notes(self):

        return self.notes

    # -----------------------------
    # Tags
    # -----------------------------

    def add_tag(self, tag):

        tag = tag.strip().lower()

        if tag and tag not in self.tags:

            self.tags.append(tag)