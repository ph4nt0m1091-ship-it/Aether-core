import re

from providers.agent_router import (
    AgentRouter
)


class AgentRouterSkill:
    """
    Lets Aether select suitable external workers
    by capability instead of exact program name.

    This skill performs routing only.

    It does not execute external agents.
    """

    name = "agent_router"

    description = (
        "Finds and selects external agents by role, "
        "installation status, and execution preferences."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.router = (
            AgentRouter(
                "."
            )
        )

        self.last_route = None

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        message = (
            message.strip()
        )

        lower = (
            message.lower()
        )

        self.last_route = None

        if lower in (
            "show agent roles",
            "list agent roles",
            "what agent roles are available"
        ):

            return self._show_roles()

        if lower in (
            "show installed agents",
            "list installed agents",
            "what agents are installed"
        ):

            return self._show_installed()

        role = self._extract_role(
            message
        )

        if role is None:

            return None

        padded = (
            " "
            + lower
            + " "
        )

        prefer_local = (
            " local "
            in padded
        )

        prefer_cloud = (
            " cloud "
            in padded
        )

        result = (
            self.router.route(
                role,
                prefer_local=(
                    prefer_local
                ),
                prefer_cloud=(
                    prefer_cloud
                )
            )
        )

        self.last_route = result

        return self._format_route(
            result
        )

    # ---------------------------------
    # EXTRACT ROLE
    # ---------------------------------

    def _extract_role(
        self,
        message
    ):

        patterns = [
            r"^find\s+(?:me\s+)?(?:an?\s+)?(.+?)\s+agent$",
            r"^find\s+(?:an?\s+)?agent\s+for\s+(.+)$",
            r"^which\s+agent\s+can\s+do\s+(.+)$",
            r"^which\s+agent\s+can\s+(.+)$",
            r"^what\s+agent\s+can\s+(.+)$",
            r"^select\s+(?:an?\s+)?(.+?)\s+agent$"
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                message,
                re.IGNORECASE
            )

            if not match:

                continue

            raw_role = (
                match.group(1)
                .strip()
                .lower()
            )

            return self._infer_role(
                raw_role
            )

        return None

    # ---------------------------------
    # INFER ROLE
    # ---------------------------------

    def _infer_role(
        self,
        text
    ):

        text = text.lower()

        # Review first so "review code"
        # does not fall into general coding.
        if any(
            phrase in text
            for phrase in (
                "review code",
                "code review",
                "review my code",
                "review"
            )
        ):

            return "code_review"

        if any(
            phrase in text
            for phrase in (
                "debug",
                "fix bug",
                "fix bugs"
            )
        ):

            return "debugging"

        if any(
            word in text
            for word in (
                "code",
                "coding",
                "program",
                "develop",
                "write software"
            )
        ):

            return "coding"

        if any(
            word in text
            for word in (
                "research",
                "look into",
                "investigate"
            )
        ):

            return "research"

        if any(
            word in text
            for word in (
                "automate",
                "automation"
            )
        ):

            return "automation"

        if "git" in text:

            return "git"

        if text in (
            "general",
            "general purpose",
            "general-purpose"
        ):

            return "general_agent"

        return self.router.normalize_role(
            text
        )

    # ---------------------------------
    # FORMAT ROUTE
    # ---------------------------------

    def _format_route(
        self,
        result
    ):

        status = result.get(
            "status"
        )

        role = result.get(
            "role",
            "unknown"
        )

        if status == "selected":

            selected = result[
                "selected"
            ]

            return (
                "Aether: Agent Router\n\n"
                f"Requested role: {role}\n"
                "Selected worker: "
                f"{selected['display_name']}\n"
                f"Profile: {selected['name']}\n"
                "Installed: yes\n"
                "Execution type: "
                f"{selected['execution_type']}\n"
                "Permission required: "
                f"{selected['requires_permission']}\n"
                "Local-model support: "
                f"{selected['local_model_support']}\n"
                "Cloud support: "
                f"{selected['cloud_support']}"
            )

        if status == "not_installed":

            output = (
                "Aether: Agent Router\n\n"
                f"Requested role: {role}\n\n"
                "No installed agent currently "
                "matches this role.\n\n"
                "Known candidates:\n"
            )

            for item in result.get(
                "candidates",
                []
            ):

                output += (
                    f"- {item['display_name']}\n"
                )

            return output.rstrip()

        if status == "capability_gap":

            return (
                "Aether: Agent Router\n\n"
                "No known external agent "
                f'supports role "{role}".'
            )

        return (
            "Aether: Agent routing failed.\n"
            f"{result.get('error', '')}"
        ).rstrip()

    # ---------------------------------
    # SHOW INSTALLED
    # ---------------------------------

    def _show_installed(
        self
    ):

        agents = (
            self.router
            .installed_agents()
        )

        if not agents:

            return (
                "Aether: No known external "
                "agents are installed."
            )

        output = (
            "Aether: Installed External Agents\n\n"
        )

        for agent in agents:

            output += (
                f"- {agent.get('display_name')}\n"
                f"  Profile: "
                f"{agent.get('name')}\n"
                f"  Roles: "
                f"{', '.join(agent.get('roles', []))}\n"
            )

        return output.rstrip()

    # ---------------------------------
    # SHOW ROLES
    # ---------------------------------

    def _show_roles(
        self
    ):

        roles = (
            self.router
            .known_roles()
        )

        output = (
            "Aether: Known Agent Roles\n\n"
        )

        for role in roles:

            output += (
                f"- {role}\n"
            )

        return output.rstrip()

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None