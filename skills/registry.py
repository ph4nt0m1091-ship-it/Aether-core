from skills.greeting_skill import GreetingSkill
from skills.memory_skill import MemorySkill
from skills.time_skill import TimeSkill
from skills.calculator_skill import CalculatorSkill
from skills.file_skill import FileSkill
from skills.web_search_skill import WebSearchSkill
from skills.research_skill import ResearchSkill
from skills.system_skill import SystemSkill
from skills.history_skill import HistorySkill
from skills.provider_skill import ProviderSkill
from skills.scheduler_skill import SchedulerSkill
from skills.runtime_skill import RuntimeSkill
from skills.terminal_skill import TerminalSkill
from skills.workflow_skill import WorkflowSkill


class SkillRegistry:
    """
    Stores and manages all of Aether's skills.

    Permission-aware workflows must be checked before
    skills that can hold their own pending permission.
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

        self.scheduler_skill = (
            SchedulerSkill(
                memory
            )
        )

        self.runtime_skill = (
            RuntimeSkill(
                memory
            )
        )

        self.provider_skill = (
            ProviderSkill(
                memory
            )
        )

        self.terminal_skill = (
            TerminalSkill(
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
            HistorySkill(memory),

            self.scheduler_skill,
            self.runtime_skill,

            # Workflow must come before any skill that
            # can hold a permission request.
            self.workflow_skill,

            self.provider_skill,
            self.terminal_skill
        ]

    # ---------------------------------
    # CONNECT MANAGER
    # ---------------------------------

    def connect_manager(
        self,
        skill_manager
    ):

        self.workflow_skill.connect(
            skill_manager
        )

        self.scheduler_skill.connect(
            skill_manager
        )

        self.runtime_skill.connect(
            skill_manager
        )

    # ---------------------------------
    # BACKGROUND SERVICES
    # ---------------------------------

    def start_background_services(
        self
    ):

        self.scheduler_skill.start()

    def stop_background_services(
        self
    ):

        self.scheduler_skill.stop()

    # ---------------------------------
    # GET SKILL
    # ---------------------------------

    def get_skill(
        self,
        name
    ):

        for skill in self.skills:

            if skill.name == name:

                return skill

        return None

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

        skill = self.get_skill(
            step["skill"]
        )

        if skill is None:

            return None

        return skill.execute(
            step
        )

    # ---------------------------------
    # AVAILABLE SKILLS
    # ---------------------------------

    def available_skills(
        self
    ):

        return [
            skill.name
            for skill in self.skills
        ]

    # ---------------------------------
    # DESCRIPTIONS
    # ---------------------------------

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