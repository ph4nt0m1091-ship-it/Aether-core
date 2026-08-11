from skills.registry import SkillRegistry


class SkillManager:
    """
    Manages all of Aether's skills.
    """

    def __init__(self, memory):

        self.memory = memory

        self.registry = SkillRegistry(memory)

    def handle(self, message):

        return self.registry.handle(message)

    def execute(self, step):

        self.registry.execute(step)

    def available_skills(self):
        """
        Returns every registered skill.
        """

        return self.registry.available_skills()