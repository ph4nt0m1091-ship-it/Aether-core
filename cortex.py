class Cortex:
    """
    Aether's executive reasoning system.

    Cortex decides WHAT should happen.

    The Brain decides HOW to make it happen.
    """

    def __init__(self):

        self.current_goal = None

    def set_goal(self, goal):

        self.current_goal = goal

    def get_goal(self):

        return self.current_goal