from skills.greeting_skill import GreetingSkill
from skills.memory_skill import MemorySkill
from skills.time_skill import TimeSkill
from skills.calculator_skill import CalculatorSkill
from skills.file_skill import FileSkill
from skills.web_search_skill import WebSearchSkill
from skills.research_skill import ResearchSkill
from skills.system_skill import SystemSkill
from skills.history_skill import HistorySkill
from skills.desktop_skill import DesktopSkill
from skills.provider_skill import ProviderSkill
from skills.agent_router_skill import AgentRouterSkill
from skills.scheduler_skill import SchedulerSkill
from skills.runtime_skill import RuntimeSkill
from skills.terminal_skill import TerminalSkill
from skills.workflow_skill import WorkflowSkill
from skills.agent_delegation_skill import AgentDelegationSkill
from skills.cloud_side_mode_skill import CloudSideModeSkill


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

        self.cloud_side_mode_skill = (
            CloudSideModeSkill(
                memory
            )
        )

        self.agent_router_skill = (
            AgentRouterSkill(
                memory
            )
        )

        self.agent_delegation_skill = (
            AgentDelegationSkill(
                memory
            )
        )

        self.provider_skill = (
            ProviderSkill(
                memory
            )
        )

        self.desktop_skill = (
            DesktopSkill(
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

            # Low-risk desktop phrases must be checked before
            # the broader SystemSkill open route so known folders
            # such as "open my downloads" reach DesktopSkill.
            self.desktop_skill,

            SystemSkill(memory),
            HistorySkill(memory),

            # Cloud commands are explicit and privacy-gated.
            self.cloud_side_mode_skill,

            self.agent_delegation_skill,
            self.agent_router_skill,

            self.scheduler_skill,
            self.runtime_skill,

            # Workflow must come before skills that can hold
            # their own pending permission.
            self.workflow_skill,

            self.provider_skill,
            self.terminal_skill
        ]

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

        self.desktop_skill.connect(
            skill_manager
        )

    def start_background_services(
        self
    ):

        self.scheduler_skill.start()

    def stop_background_services(
        self
    ):

        self.scheduler_skill.stop()

    def get_skill(
        self,
        name
    ):

        for skill in self.skills:

            if skill.name == name:

                return skill

        return None

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
