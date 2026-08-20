import subprocess

from providers.agent_delegator import (
    AgentDelegator
)


class AgentDelegationSkill:
    """
    Handles natural-language delegation to
    external-agent roles.

    Invocation Adapter v1:

    - selects worker
    - builds exact provider command
    - displays safe preview
    - DOES NOT execute yet
    """

    name = "agent_delegation"

    description = (
        "Plans natural-language delegation "
        "and builds provider-specific "
        "external-agent invocations."
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

        lower = (
            message.lower()
        )

        if not (
            lower.startswith(
                "ask "
            )
            or lower.startswith(
                "delegate "
            )
        ):

            return None

        # Keep existing Ollama behavior.
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
    # FORMAT COMMAND
    # ---------------------------------

    def _format_command(
        self,
        command
    ):

        if not isinstance(
            command,
            list
        ):

            return str(
                command
            )

        return subprocess.list2cmdline(
            [
                str(item)
                for item in command
            ]
        )

    # ---------------------------------
    # FORMAT PLAN
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
        # INVOCATION BUILT
        # ---------------------------------

        if status == "invocation_built":

            selected = result.get(
                "selected",
                {}
            )

            invocation = result.get(
                "invocation",
                {}
            )

            command = (
                self._format_command(
                    invocation.get(
                        "command",
                        []
                    )
                )
            )

            output = (
                "Aether: Agent Delegation Preview\n\n"
                f"Task: {task}\n"
                f"Role: {role}\n"
                "Selected worker: "
                f"{selected.get('display_name')}\n"
                "Profile: "
                f"{selected.get('name')}\n"
                "Adapter: "
                f"{invocation.get('adapter')}\n\n"
                "Proposed command:\n"
                f"{command}\n\n"
                "Permission required: "
                f"{result.get('requires_permission')}\n"
                "Execution ready: "
                f"{result.get('execution_ready')}\n"
            )

            if not result.get(
                "execution_ready"
            ):

                output += (
                    "\nExecution remains locked.\n"
                    + invocation.get(
                        "execution_block_reason",
                        (
                            "This invocation has "
                            "not yet passed its "
                            "safety test."
                        )
                    )
                )

            output += (
                "\n\nNothing was executed."
            )

            return output

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

            for candidate in result.get(
                "candidates",
                []
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
        # NO ADAPTER
        # ---------------------------------

        if status == "invocation_unavailable":

            selected = result.get(
                "selected",
                {}
            )

            return (
                "Aether: Agent Delegation\n\n"
                f"Task: {task}\n"
                f"Role: {role}\n"
                "Selected worker: "
                f"{selected.get('display_name')}\n\n"
                "The worker is installed, but "
                "Aether does not have a ready "
                "invocation adapter for it yet.\n\n"
                f"{result.get('error', '')}"
            ).rstrip()

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