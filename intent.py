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

        if (
            message.startswith("what's next")
            or message.startswith("whats next")
            or message.startswith("next step")
        ):

            return "next_step"

        # ----------------------------
        # Goal commands
        # ----------------------------

        if message.startswith("set goal "):

            return "set_goal"

        # ----------------------------
        # Mission commands
        # ----------------------------

        mission_words = [
            "start",
            "build",
            "create",
            "make"
        ]

        if any(
            message.startswith(word)
            for word in mission_words
        ):

            return "mission"

        # ----------------------------
        # Known skill requests
        # ----------------------------

        known_skill_requests = [
            "calculate ",
            "what is ",
            "what's ",
            "what time is it",
            "tell me the time",
            "current time",
            "what's my name",
            "whats my name",
            "what is my name",
            "what is my favorite color",
            "what's my favorite color",
            "what do i like",
            "hello",
            "hi",
            "hey",
            "search the web for ",
            "search web for ",
            "search for "
        ]

        if any(
            message.startswith(word)
            for word in known_skill_requests
        ):

            return "skill_request"

        # ----------------------------
        # Capability requests
        # ----------------------------
        #
        # These are requests that imply
        # an action/capability which may or
        # may not exist yet.

        capability_requests = [
            "search the web",
            "search online",
            "browse the web",
            "browse online",
            "open a website",
            "go to a website",
            "send an email",
            "send a message",
            "download ",
            "upload ",
            "play music",
            "play a video",
            "take a screenshot",
            "open an app",
            "launch an app",
            "control the computer",
            "click ",
            "type ",
            "read this website",
            "look this up"
        ]

        if any(
            phrase in message
            for phrase in capability_requests
        ):

            return "capability_request"

        # ----------------------------
        # Conversation
        # ----------------------------

        return "conversation"