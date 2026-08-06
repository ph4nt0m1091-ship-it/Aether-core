from skills.greeting_skill import GreetingSkill
from skills.memory_skill import MemorySkill
from skills.calculator_skill import CalculatorSkill
from skills.time_skill import TimeSkill
from skills.file_skill import FileSkill


class SkillManager:
    """
    Routes messages and mission steps
    to the correct skill.
    """

    def __init__(self, memory):

        self.skills = {
            "greeting": GreetingSkill(memory),
            "memory": MemorySkill(memory),
           "calculator": CalculatorSkill(memory),
           "time": TimeSkill(memory),
            "file": FileSkill()
        }

    def handle(self, message):

        for skill in self.skills.values():

            if hasattr(skill, "handle"):

                response = skill.handle(message)

                if response:
                    return response

        return None

    def execute(self, step):

        skill_name = step["skill"]

        skill = self.skills.get(skill_name)

        if skill is None:

            print(f"Aether: Unknown skill '{skill_name}'")
            return

        if hasattr(skill, "execute"):

            skill.execute(step)

        else:

            print(f"Aether: Skill '{skill_name}' cannot execute tasks.")