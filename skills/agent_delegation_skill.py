import subprocess

from permissions.permission_manager import (
    PermissionManager
)

from providers.agent_delegator import (
    AgentDelegator
)


class AgentDelegationSkill:
    """
    Handles natural-language delegation to
    external-agent roles.

    Permission Bridge v1:

    - selects a worker
    - builds the provider-specific invocation
    - requests explicit Aether permission
    - supports yes / no responses
    - deliberately keeps execution locked

    No external agent is launched by this version.
    """

    name = "agent_delegation"

    description = (
        "Plans natural-language delegation, "
        "builds provider-specific invocations, "
        "and protects them with explicit permission."
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

        self.permissions = (
            PermissionManager()
        )

        self.last_plan = None

        self.last_execution_result = None

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        self.last_execution_result = None

        message = str(
            message or ""
        ).strip()

        lower = (
            message.lower()
        )

        # ---------------------------------
        # PENDING DELEGATION PERMISSION
        # ---------------------------------

        if self.permissions.has_pending():

            response = (
                self.permissions
                .interpret_response(
                    message
                )
            )

            if response == "approve":

                pending = (
                    self.permissions
                    .consume()
                )

                return (
                    self._handle_approval(
                        pending
                    )
                )

            if response == "deny":

                self.permissions.cancel()

                return (
                    "Aether: Agent delegation "
                    "cancelled.\n\n"
                    "Nothing was executed."
                )

            return (
                "Aether: I am waiting for "
                "delegation permission.\n"
                'Say "yes" to approve or '
                '"no" to cancel.'
            )

        # ---------------------------------
        # NEW DELEGATION
        # ---------------------------------

        if not (
            lower.startswith(
                "ask "
            )
            or lower.startswith(
                "delegate "
            )
        ):

            return None

        # Preserve existing Ollama syntax.
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

        return (
            self._handle_plan(
                result
            )
        )

    # ---------------------------------
    # HANDLE PLAN
    # ---------------------------------

    def _handle_plan(
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

            invocation = result.get(
                "invocation",
                {}
            )

            selected = result.get(
                "selected",
                {}
            )

            command = invocation.get(
                "command",
                []
            )

            formatted_command = (
                self._format_command(
                    command
                )
            )

            # Store the exact structured plan
            # behind the permission request.
            #
            # Do not store permission itself
            # anywhere persistent.
            self.permissions.request(
                "agent_delegation_execution",
                {
                    "provider": (
                        result.get(
                            "provider"
                        )
                    ),
                    "role": role,
                    "task": task,
                    "command": list(
                        command
                    ),
                    "invocation": invocation
                }
            )

            return (
                "Aether: Permission required.\n\n"
                "Delegated task:\n"
                f"{task}\n\n"
                "Role: "
                f"{role}\n"
                "External agent: "
                f"{selected.get('display_name')}\n"
                "Profile: "
                f"{selected.get('name')}\n\n"
                "Proposed command:\n"
                f"{formatted_command}\n\n"
                "External agents may read, "
                "create, or modify project files "
                "depending on their available "
                "tools and instructions.\n\n"
                "Execution safety lock: ON\n\n"
                'Say "yes" to approve or '
                '"no" to cancel.'
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
        # NO INVOCATION ADAPTER
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

        # ---------------------------------
        # OTHER FAILURE
        # ---------------------------------

        return (
            "Aether: Agent Delegation\n\n"
            f"Task role: {role}\n"
            f"{result.get('error', 'Delegation failed.')}"
        )

    # ---------------------------------
    # HANDLE APPROVAL
    # ---------------------------------

    def _handle_approval(
        self,
        pending
    ):

        if not isinstance(
            pending,
            dict
        ):

            return (
                "Aether: Delegation permission "
                "data was invalid.\n\n"
                "Nothing was executed."
            )

        action = pending.get(
            "action"
        )

        data = pending.get(
            "data",
            {}
        )

        if action != (
            "agent_delegation_execution"
        ):

            return (
                "Aether: The pending delegation "
                "action was not recognized.\n\n"
                "Nothing was executed."
            )

        invocation = data.get(
            "invocation",
            {}
        )

        provider = data.get(
            "provider",
            "unknown"
        )

        task = data.get(
            "task",
            ""
        )

        command = data.get(
            "command",
            []
        )

        formatted_command = (
            self._format_command(
                command
            )
        )

        # ---------------------------------
        # SAFETY LOCK
        # ---------------------------------
        #
        # Permission routing is being tested
        # before natural-agent execution is
        # enabled.
        #
        # Even an approved request MUST stop
        # here in Permission Bridge v1.

        result = {
            "success": False,
            "status": (
                "approved_but_locked"
            ),
            "provider": provider,
            "task": task,
            "command": command,
            "approved": True,
            "executed": False,
            "execution_ready": (
                invocation.get(
                    "execution_ready",
                    False
                )
            ),
            "reason": (
                "Delegation permission was "
                "approved, but natural-agent "
                "execution remains safety-locked."
            )
        }

        self.last_execution_result = (
            result
        )

        return (
            "Aether: Delegation approved.\n\n"
            f"External agent: {provider}\n"
            f"Task: {task}\n\n"
            "Approved command:\n"
            f"{formatted_command}\n\n"
            "Execution safety lock: ON\n\n"
            "The permission bridge worked, "
            "but external execution is still "
            "disabled for this safety test.\n\n"
            "Nothing was executed."
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
    # PENDING PERMISSION
    # ---------------------------------

    def has_pending_permission(
        self
    ):

        return (
            self.permissions
            .has_pending()
        )

    # ---------------------------------
    # CANCEL PERMISSION
    # ---------------------------------

    def cancel_pending_permission(
        self
    ):

        if not (
            self.permissions
            .has_pending()
        ):

            return False

        self.permissions.cancel()

        return True

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None