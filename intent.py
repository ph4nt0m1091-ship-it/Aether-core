class IntentAnalyzer:
    """
    Determines what the user is trying to do.
    """

    def analyze(self, message):

        message = message.lower().strip()

        if any(word in message for word in (
            "robot",
            "robotics",
            "robotic"
        )):

            return "mission"

        return "conversation"