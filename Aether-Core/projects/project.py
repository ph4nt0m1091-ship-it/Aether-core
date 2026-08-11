from datetime import datetime


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

        self.activity = []

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

    # -----------------------------
    # Activity
    # -----------------------------

    def add_activity(self, activity):

        activity = activity.strip()

        if not activity:

            return

        event = {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "message": activity
        }

        self.activity.append(event)

    def get_activity(self):

        return self.activity