from providers.agent_delegator import (
    AgentDelegator
)


class AgentDelegationSkill:
    """
    Handles natural-language delegation to
    external-agent roles.

    v1 plans and routes delegation.

    It intentionally does not execute natural
    tasks until an agent-specific invocation
    adapter is available.
    """

    name = "agent_delegation"

    description = (
        "Plans natural-language delegation to "
        "suitable external agents."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.delegator = (
            AgentDelegator(
                "."
            )
        )

        self.last_plan = None

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        message = str(
            message or ""
        ).strip()

        lower = message.lower()

        if not (
            lower.startswith(
                "ask "
            )
            or lower.startswith(
                "delegate "
            )
        ):

            return None

        # Preserve existing direct Ollama syntax.
        if lower.startswith(
            "ask ollama "
        ):

            return None

        result = (
            self.delegator
            .build_plan(
                message
            )
        )

        if result.get(
            "status"
        ) == "not_delegation":

            return None

        self.last_plan = result

        return self._format_plan(
            result
        )

    # ---------------------------------
    # FORMAT
    # ---------------------------------

    def _format_plan(
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

        task = result.get(
            "task",
            ""
        )

        # ---------------------------------
        # INSTALLED WORKER SELECTED
        # ---------------------------------

        if status == "planned":

            selected = result.get(
                "selected",
                {}
            )

            return (
                "Aether: Agent Delegation Plan\n\n"
                f"Task: {task}\n"
                f"Role: {role}\n"
                "Selected worker: "
                f"{selected.get('display_name')}\n"
                "Profile: "
                f"{selected.get('name')}\n"
                "Installed: yes\n"
                "Permission required: "
                f"{selected.get('requires_permission')}\n\n"
                "Routing is ready.\n"
                "Natural-task execution is not "
                "enabled for this worker yet, "
                "so nothing was executed."
            )

        # ---------------------------------
        # NO INSTALLED WORKER
        # ---------------------------------

        if status == "worker_not_installed":

            output = (
                "Aether: Agent Delegation\n\n"
                f"Task: {task}\n"
                f"Role: {role}\n\n"
                "No installed worker currently "
                "matches this task.\n\n"
                "Known candidates:\n"
            )

            for candidate in (
                result.get(
                    "candidates",
                    []
                )
            ):

                output += (
                    "- "
                    + candidate.get(
                        "display_name",
                        candidate.get(
                            "name",
                            "Unknown"
                        )
                    )
                    + "\n"
                )

            return output.rstrip()

        # ---------------------------------
        # CAPABILITY GAP / FAILURE
        # ---------------------------------

        return (
            "Aether: Agent Delegation\n\n"
            f"Task role: {role}\n"
            f"{result.get('error', 'Delegation failed.')}"
        )

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None