class MemorySkill:
    """
    Handles memory-related conversation.
    """

    name = "memory"

    def __init__(self, memory):

        self.memory = memory

    def handle(self, message):

        message = message.lower().strip()

        # -------------------
        # NAME
        # -------------------

        if (
            "what's my name" in message
            or "whats my name" in message
            or "what is my name" in message
        ):

            name = self.memory.get_name()

            if name:
                return f"Aether: Your name is {name}."

            return "Aether: I don't know your name yet."

        # -------------------
        # FAVORITE COLOR
        # -------------------

        if "favorite color" in message:

            color = self.memory.get_favorite_color()

            if color:
                return f"Aether: Your favorite color is {color}."

            return "Aether: I don't know your favorite color yet."

        # -------------------
        # DOG
        # -------------------

        if "dog" in message and "name" in message:

            dog = self.memory.get_dog_name()

            if dog:
                return f"Aether: Your dog's name is {dog}."

            return "Aether: I don't know your dog's name."

        # -------------------
        # LIKES
        # -------------------

        if "what do i like" in message:

            likes = self.memory.get_likes()

            if likes:
                return "Aether: You like " + ", ".join(likes) + "."

            return "Aether: I don't know what you like yet."

        return None

    def execute(self, step):
        """
        MemorySkill is not used by missions.
        """

        return None