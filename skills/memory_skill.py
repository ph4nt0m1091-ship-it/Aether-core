import re


class MemorySkill:
    """
    Handles durable-memory retrieval.

    Memory writes are handled by Memory.remember() in main.py
    before normal skill routing so explicit remember/forget
    requests are deterministic and do not depend on an AI model.
    """

    name = "memory"

    description = (
        "Retrieves information stored in Aether's long-term memory."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory

    def handle(
        self,
        message
    ):

        original = str(
            message or ""
        ).strip()

        if not original:

            return None

        lower = (
            original.lower()
            .strip()
        )

        # -------------------
        # MEMORY SUMMARY
        # -------------------

        summary_requests = (
            "what do you remember about me",
            "what do you remember about me?",
            "what do you remember",
            "what do you remember?",
            "show my memory",
            "show what you remember about me",
            "tell me what you remember about me"
        )

        if lower in summary_requests:

            lines = (
                self.memory
                .summary_lines()
            )

            if not lines:

                return (
                    "Aether: I don't have any "
                    "long-term memories about you yet."
                )

            return (
                "Aether: Here's what I remember:\n\n"
                + "\n".join(
                    f"- {line}"
                    for line in lines
                )
            )

        # -------------------
        # NAME
        # -------------------

        if (
            "what's my name" in lower
            or "whats my name" in lower
            or "what is my name" in lower
        ):

            name = (
                self.memory
                .get_name()
            )

            if name:

                return (
                    f"Aether: Your name is {name}."
                )

            return (
                "Aether: I don't know your name yet."
            )

        # -------------------
        # FAVORITE COLOR
        # -------------------

        if "favorite color" in lower:

            color = (
                self.memory
                .get_favorite_color()
            )

            if color:

                return (
                    "Aether: Your favorite color "
                    f"is {color}."
                )

            return (
                "Aether: I don't know your "
                "favorite color yet."
            )

        # -------------------
        # DOG
        # -------------------

        if (
            "dog" in lower
            and "name" in lower
        ):

            dog = (
                self.memory
                .get_dog_name()
            )

            if dog:

                return (
                    "Aether: Your dog's name "
                    f"is {dog}."
                )

            return (
                "Aether: I don't know your "
                "dog's name."
            )

        # -------------------
        # LIKES
        # -------------------

        if (
            "what do i like" in lower
            or "what things do i like" in lower
        ):

            likes = (
                self.memory
                .get_likes()
            )

            if likes:

                return (
                    "Aether: You like "
                    + ", ".join(
                        likes
                    )
                    + "."
                )

            return (
                "Aether: I don't know what "
                "you like yet."
            )

        # -------------------
        # MAIN PROJECT
        # -------------------

        if (
            "what is my main project" in lower
            or "what's my main project" in lower
            or "whats my main project" in lower
        ):

            project = (
                self.memory
                .get_main_project()
            )

            if project:

                return (
                    "Aether: Your main project "
                    f"is {project}."
                )

            return (
                "Aether: I don't know your "
                "main project yet."
            )

        # -------------------
        # GENERIC "WHAT IS MY X?"
        # -------------------

        match = re.match(
            r"^what(?:'s| is)\s+my\s+(.+?)\??$",
            lower
        )

        if match:

            raw_key = (
                match.group(
                    1
                )
                .strip()
            )

            value = (
                self.memory
                .get_fact(
                    raw_key
                )
            )

            if value is not None:

                return (
                    f"Aether: Your {raw_key} is {value}."
                )

            return (
                f"Aether: I don't have your "
                f"{raw_key} stored yet."
            )

        return None

    def execute(
        self,
        step
    ):
        """
        MemorySkill is not used by missions.
        """

        return None
