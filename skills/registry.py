from skills.greeting_skill import GreetingSkill
from skills.memory_skill import MemorySkill
from skills.time_skill import TimeSkill
from skills.calculator_skill import CalculatorSkill
from skills.file_skill import FileSkill
from skills.web_search_skill import WebSearchSkill
from skills.research_skill import ResearchSkill
from skills.system_skill import SystemSkill
from skills.terminal_skill import TerminalSkill
from skills.workflow_skill import WorkflowSkill


class SkillRegistry:
    """
    Stores and manages all of Aether's skills.
    """

    def __init__(
        self,
        memory
    ):

        self.workflow_skill = (
            WorkflowSkill(
                memory
            )
        )

        self.skills = [
            GreetingSkill(memory),
            MemorySkill(memory),
            TimeSkill(memory),
            CalculatorSkill(memory),
            FileSkill(memory),
            WebSearchSkill(memory),
            ResearchSkill(memory),
            SystemSkill(memory),
            TerminalSkill(memory),
            self.workflow_skill
        ]

    # ---------------------------------
    # CONNECT SKILL MANAGER
    # ---------------------------------

    def connect_manager(
        self,
        skill_manager
    ):

        self.workflow_skill.connect(
            skill_manager
        )

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        for skill in self.skills:

            response = skill.handle(
                message
            )

            if response is not None:

                return response

        return None

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        for skill in self.skills:

            if (
                skill.name
                == step["skill"]
            ):

                return skill.execute(
                    step
                )

        return None

    def available_skills(
        self
    ):

        return [
            skill.name
            for skill in self.skills
        ]

    def describe_skills(
        self
    ):

        return [
            {
                "name": skill.name,
                "description": getattr(
                    skill,
                    "description",
                    "No description available."
                )
            }
            for skill in self.skills
        ]