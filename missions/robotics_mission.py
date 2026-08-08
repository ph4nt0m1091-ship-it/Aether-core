from missions.mission import Mission
from task import Task


class RoboticsMission(Mission):
    """
    Creates a robotics project mission.
    """

    keyword = "robotics"
    name = "Start Robotics Project"

    def build(self):

        task = Task(self.name)

        # ----------------------------
        # Create Robotics Workspace
        # ----------------------------

        task.add_step(
            "file",
            "create_folder",
            name="robotics"
        )

        task.add_step(
            "file",
            "create_file",
            filename="robotics/README.md"
        )

        task.add_step(
            "file",
            "create_file",
            filename="robotics/main.py"
        )

        task.add_step(
            "file",
            "create_file",
            filename="robotics/notes.txt"
        )

        return task