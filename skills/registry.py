from skills.greeting_skill import GreetingSkill
from skills.memory_skill import MemorySkill
from skills.time_skill import TimeSkill
from skills.calculator_skill import CalculatorSkill
from skills.file_skill import FileSkill


class SkillRegistry:
    """
    Aether's Skill Lab registry.

    Stores, discovers, and manages Aether's available skills.
    """

    def __init__(self, memory):

        self.memory = memory

        # ---------------------------------
        # Skill Lab
        # ---------------------------------

        self.skills = []

        self.register(
            GreetingSkill(memory)
        )

        self.register(
            MemorySkill(memory)
        )

        self.register(
            TimeSkill(memory)
        )

        self.register(
            CalculatorSkill(memory)
        )

        self.register(
            FileSkill(memory)
        )

    # ---------------------------------
    # REGISTER
    # ---------------------------------

    def register(self, skill):
        """
        Register a new skill with Aether.
        """

        if skill is None:
            return False

        if not hasattr(skill, "name"):
            return False

        for existing in self.skills:

            if existing.name == skill.name:
                return False

        self.skills.append(skill)

        return True

    # ---------------------------------
    # FIND
    # ---------------------------------

    def get_skill(self, name):
        """
        Find a skill by name.
        """

        name = name.lower().strip()

        for skill in self.skills:

            if skill.name.lower() == name:
                return skill

        return None

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(self, message):

        for skill in self.skills:

            response = skill.handle(message)

            if response is not None:

                return response

        return None

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(self, step):

        skill_name = step.get(
            "skill"
        )

        skill = self.get_skill(
            skill_name
        )

        if skill is None:
            return None

        return skill.execute(
            step
        )

    # ---------------------------------
    # AVAILABLE SKILLS
    # ---------------------------------

    def available_skills(self):
        """
        Return the names of every
        registered skill.
        """

        return [
            skill.name
            for skill in self.skills
        ]

    # ---------------------------------
    # SKILL INFORMATION
    # ---------------------------------

    def describe_skills(self):
        """
        Return basic capability information
        about every registered skill.
        """

        descriptions = []

        for skill in self.skills:

            description = getattr(
                skill,
                "description",
                "No description available."
            )

            descriptions.append({
                "name": skill.name,
                "description": description
            })

        return descriptions