from task import Task


class RoboticsMission:
    """
    Creates a robotics project mission.
    """

    def build(self):

        task = Task("Start Robotics Project")

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