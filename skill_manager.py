from skills.registry import SkillRegistry


class SkillManager:
    """
    Manages all of Aether's skills.
    """

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.registry = (
            SkillRegistry(
                memory
            )
        )

        self.registry.connect_manager(
            self
        )

    def handle(
        self,
        message
    ):

        return self.registry.handle(
            message
        )

    def execute(
        self,
        step
    ):

        return self.registry.execute(
            step
        )

    def available_skills(
        self
    ):

        return (
            self.registry
            .available_skills()
        )