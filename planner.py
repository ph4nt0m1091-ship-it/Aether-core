from missions.registry import MissionRegistry


class Planner:
    """
    Chooses the correct mission using the Mission Registry.
    """

    def __init__(self):

        self.registry = MissionRegistry()

    def create_task(self, goal):

        mission = self.registry.get(goal)

        if mission:
            return mission.build()

        return None

    def available_missions(self):
        """
        Returns all available mission names.
        """

        return self.registry.list_missions()