from missions.robotics_mission import RoboticsMission


class Planner:
    """
    Decides which mission should build the task.
    """

    def __init__(self):

        self.robotics = RoboticsMission()

    def create_task(self, goal):

        goal = goal.lower()

        if "robotics" in goal:

            return self.robotics.build()

        return None