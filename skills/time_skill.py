from tools.clock_tool import ClockTool


class TimeSkill:
    """
    Handles time-related questions.
    """

    name = "time"

    def __init__(self, memory):

        self.memory = memory
        self.clock = ClockTool()

    def handle(self, message):

        message = message.lower().strip()

        if (
            "what time is it" in message
            or "tell me the time" in message
            or "current time" in message
        ):

            current_time = self.clock.get_time()

            return f"Aether: The current time is {current_time}."

        return None

    def execute(self, step):
        """
        TimeSkill is not used by missions.
        """

        return None