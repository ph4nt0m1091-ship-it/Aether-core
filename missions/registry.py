from missions.robotics_mission import RoboticsMission


class MissionRegistry:
    """
    Stores and returns available missions.
    """

    def __init__(self):

        self.missions = {
            "robotics": RoboticsMission()
        }

    def get(self, goal):

        goal = goal.lower()

        for keyword, mission in self.missions.items():

            if keyword in goal:
                return mission

        return None

    def available_missions(self):
        """
        Returns the registered mission keywords.
        """
        return list(self.missions.keys())

    def list_missions(self):
        """
        Returns the names of all registered missions.
        """
        return [mission.name for mission in self.missions.values()]