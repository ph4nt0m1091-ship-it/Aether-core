class IntentAnalyzer:
    """
    Determines what the user is trying to do.
    """

    def analyze(self, message):

        message = message.lower().strip()

        # ----------------------------
        # Progress commands
        # ----------------------------

        if message.startswith("complete step"):

            return "complete_step"

        # ----------------------------
        # Planning commands
        # ----------------------------

        if message.startswith("show plan"):

            return "show_plan"

        # ----------------------------
        # Mission commands
        # ----------------------------

        mission_words = [
            "start",
            "build",
            "create",
            "make"
        ]

        if any(message.startswith(word) for word in mission_words):

            return "mission"

        return "conversation"