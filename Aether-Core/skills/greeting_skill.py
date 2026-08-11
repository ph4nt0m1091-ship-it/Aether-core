class GreetingSkill:
    """
    Handles greetings and farewells.
    """

    name = "greeting"

    def __init__(self, memory):

        self.memory = memory

    def handle(self, message):

        message = message.lower().strip()

        greetings = [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening"
        ]

        if any(message.startswith(greeting) for greeting in greetings):

            name = self.memory.get_name()

            if name:
                return f"Aether: Hello, {name}! It's good to see you."

            return "Aether: Hello! It's good to see you."

        if "good night" in message:

            name = self.memory.get_name()

            if name:
                return f"Aether: Good night, {name}. Sleep well."

            return "Aether: Good night. Sleep well."

        return None

    def execute(self, step):
        """
        GreetingSkill is not used by missions.
        """

        return None