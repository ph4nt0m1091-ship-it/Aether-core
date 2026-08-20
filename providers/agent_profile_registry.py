from providers.agent_profile import (
    AgentProfile
)


class AgentProfileRegistry:
    """
    Stores external-agent profiles known to Aether.

    Profiles are independent from installation status.

    An agent can exist here even when it is not currently
    installed on the machine.
    """

    def __init__(
        self
    ):

        self.profiles = {}

        self._load_defaults()

    # ---------------------------------
    # DEFAULT PROFILES
    # ---------------------------------

    def _load_defaults(
        self
    ):

        defaults = [
            AgentProfile(
                name="hermes",
                display_name="Hermes",
                description=(
                    "General autonomous agent capable "
                    "of handling broader multi-step work."
                ),
                executables=[
                    "hermes"
                ],
                roles=[
                    "general_agent",
                    "research",
                    "automation"
                ],
                execution_type="cli",
                requires_permission=True,
                local_model_support=True,
                cloud_support=True
            ),

            AgentProfile(
                name="opencode",
                display_name="OpenCode",
                description=(
                    "Coding-focused external agent "
                    "with local and remote model options."
                ),
                executables=[
                    "opencode"
                ],
                roles=[
                    "coding",
                    "debugging",
                    "code_review"
                ],
                execution_type="cli",
                requires_permission=True,
                local_model_support=True,
                cloud_support=True
            ),

            AgentProfile(
                name="claude_code",
                display_name="Claude Code",
                description=(
                    "Coding agent designed for "
                    "software-development tasks."
                ),
                executables=[
                    "claude"
                ],
                roles=[
                    "coding",
                    "debugging",
                    "code_review"
                ],
                execution_type="cli_cloud",
                requires_permission=True,
                local_model_support=False,
                cloud_support=True
            ),

            AgentProfile(
                name="codex_cli",
                display_name="Codex",
                description=(
                    "OpenAI coding agent for "
                    "software-development tasks."
                ),
                executables=[
                    "codex"
                ],
                roles=[
                    "coding",
                    "debugging",
                    "code_review"
                ],
                execution_type="cli_cloud",
                requires_permission=True,
                local_model_support=False,
                cloud_support=True
            ),

            AgentProfile(
                name="aider",
                display_name="Aider",
                description=(
                    "Git-oriented coding assistant "
                    "with local-model support."
                ),
                executables=[
                    "aider"
                ],
                roles=[
                    "coding",
                    "debugging",
                    "git"
                ],
                execution_type="cli",
                requires_permission=True,
                local_model_support=True,
                cloud_support=True
            ),

            AgentProfile(
                name="goose",
                display_name="Goose",
                description=(
                    "General development and automation "
                    "agent with extensible tooling."
                ),
                executables=[
                    "goose"
                ],
                roles=[
                    "coding",
                    "automation",
                    "general_agent"
                ],
                execution_type="cli",
                requires_permission=True,
                local_model_support=True,
                cloud_support=True
            )
        ]

        for profile in defaults:

            self.register(
                profile
            )

    # ---------------------------------
    # REGISTER
    # ---------------------------------

    def register(
        self,
        profile
    ):

        if profile is None:

            return False

        name = getattr(
            profile,
            "name",
            ""
        ).strip()

        if not name:

            return False

        self.profiles[
            name
        ] = profile

        return True

    # ---------------------------------
    # GET
    # ---------------------------------

    def get(
        self,
        name
    ):

        if not name:

            return None

        return self.profiles.get(
            str(
                name
            ).strip().lower()
        )

    # ---------------------------------
    # ALL
    # ---------------------------------

    def all(
        self
    ):

        return list(
            self.profiles.values()
        )

    # ---------------------------------
    # ENABLED
    # ---------------------------------

    def enabled(
        self
    ):

        return [
            profile
            for profile in (
                self.profiles.values()
            )
            if profile.enabled
        ]

    # ---------------------------------
    # FIND BY ROLE
    # ---------------------------------

    def find_by_role(
        self,
        role
    ):

        role = str(
            role
        ).strip().lower()

        matches = []

        for profile in (
            self.enabled()
        ):

            roles = [
                str(item).lower()
                for item in profile.roles
            ]

            if role in roles:

                matches.append(
                    profile
                )

        return matches

    # ---------------------------------
    # INFO
    # ---------------------------------

    def info(
        self
    ):

        return [
            profile.to_dict()
            for profile in (
                self.enabled()
            )
        ]