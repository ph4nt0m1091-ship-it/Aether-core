from skills.greeting_skill import GreetingSkill
from skills.memory_skill import MemorySkill
from skills.time_skill import TimeSkill
from skills.calculator_skill import CalculatorSkill
from skills.file_skill import FileSkill


def load_skills(memory):

    return [
        GreetingSkill(memory),
        MemorySkill(memory),
        TimeSkill(memory),
        CalculatorSkill(memory),
        FileSkill(memory)
    ]