from providers.agent_profile_registry import (
    AgentProfileRegistry
)

from providers.external_agent_registry import (
    ExternalAgentRegistry
)


class AgentRouter:
    """
    Selects external agents for Aether tasks.

    Routing considers:
    - requested role
    - installation status
    - local-model support
    - cloud support
    - permission requirement

    AgentRouter does not execute agents.
    """

    ROLE_ALIASES = {
        "code": "coding",
        "coder": "coding",
        "coding": "coding",
        "programming": "coding",
        "developer": "coding",

        "debug": "debugging",
        "debugger": "debugging",
        "debugging": "debugging",

        "review": "code_review",
        "code review": "code_review",
        "code_review": "code_review",

        "research": "research",
        "researcher": "research",

        "automation": "automation",
        "automate": "automation",

        "general": "general_agent",
        "general agent": "general_agent",
        "general_agent": "general_agent",

        "git": "git"
    }

    def __init__(
        self,
        project_directory=None
    ):

        self.profile_registry = (
            AgentProfileRegistry()
        )

        self.external_registry = (
            ExternalAgentRegistry(
                project_directory
            )
        )

    # ---------------------------------
    # NORMALIZE ROLE
    # ---------------------------------

    def normalize_role(
        self,
        role
    ):

        role = str(
            role or ""
        ).strip().lower()

        return self.ROLE_ALIASES.get(
            role,
            role
        )

    # ---------------------------------
    # ROUTE
    # ---------------------------------

    def route(
        self,
        role,
        prefer_local=False,
        prefer_cloud=False
    ):

        role = self.normalize_role(
            role
        )

        if not role:

            return {
                "success": False,
                "status": "invalid_role",
                "error": (
                    "No agent role was provided."
                )
            }

        profiles = (
            self.profile_registry
            .find_by_role(
                role
            )
        )

        if not profiles:

            return {
                "success": False,
                "status": "capability_gap",
                "role": role,
                "installed": [],
                "candidates": [],
                "error": (
                    "No known external-agent profile "
                    f'supports role "{role}".'
                )
            }

        discovery = {
            item["name"]: item
            for item in (
                self.external_registry
                .discovery_report()
            )
        }

        ranked = []

        for profile in profiles:

            discovered = (
                discovery.get(
                    profile.name,
                    {}
                )
            )

            installed = bool(
                discovered.get(
                    "installed",
                    False
                )
            )

            score = 0

            if installed:

                score += 100

            if prefer_local:

                if profile.local_model_support:

                    score += 25

                else:

                    score -= 10

            if prefer_cloud:

                if profile.cloud_support:

                    score += 25

                else:

                    score -= 10

            if profile.requires_permission:

                score -= 1

            ranked.append(
                {
                    "name": (
                        profile.name
                    ),
                    "display_name": (
                        profile.display_name
                    ),
                    "description": (
                        profile.description
                    ),
                    "roles": list(
                        profile.roles
                    ),
                    "installed": (
                        installed
                    ),
                    "executable": (
                        discovered.get(
                            "executable"
                        )
                    ),
                    "execution_type": (
                        profile.execution_type
                    ),
                    "requires_permission": (
                        profile
                        .requires_permission
                    ),
                    "local_model_support": (
                        profile
                        .local_model_support
                    ),
                    "cloud_support": (
                        profile.cloud_support
                    ),
                    "score": score
                }
            )

        ranked.sort(
            key=lambda item: (
                item["score"],
                item["display_name"]
            ),
            reverse=True
        )

        installed = [
            item
            for item in ranked
            if item["installed"]
        ]

        if installed:

            selected = (
                installed[0]
            )

            return {
                "success": True,
                "status": "selected",
                "role": role,
                "selected": selected,
                "installed": installed,
                "candidates": ranked,
                "preference": {
                    "local": (
                        bool(
                            prefer_local
                        )
                    ),
                    "cloud": (
                        bool(
                            prefer_cloud
                        )
                    )
                }
            }

        return {
            "success": False,
            "status": "not_installed",
            "role": role,
            "selected": None,
            "installed": [],
            "candidates": ranked,
            "error": (
                "Suitable external agents are known, "
                "but none are currently installed."
            ),
            "preference": {
                "local": bool(
                    prefer_local
                ),
                "cloud": bool(
                    prefer_cloud
                )
            }
        }

    # ---------------------------------
    # INSTALLED AGENTS
    # ---------------------------------

    def installed_agents(
        self
    ):

        return [
            item
            for item in (
                self.external_registry
                .discovery_report()
            )
            if item.get(
                "installed"
            )
        ]

    # ---------------------------------
    # KNOWN ROLES
    # ---------------------------------

    def known_roles(
        self
    ):

        roles = set()

        for profile in (
            self.profile_registry
            .enabled()
        ):

            for role in profile.roles:

                roles.add(
                    role
                )

        return sorted(
            roles
        )