class Command:

    def __init__(self, message):

        self.message = message
        self.intent = None
        self.goal = None
        self.context = {}

    def set_intent(self, intent):

        self.intent = intent

    def set_goal(self, goal):

        self.goal = goal

    def add_context(self, key, value):

        self.context[key] = value

    def __str__(self):

        return (
            f"Command("
            f"message={self.message!r}, "
            f"intent={self.intent!r}, "
            f"goal={self.goal!r}, "
            f"context={self.context}"
            f")"
        )