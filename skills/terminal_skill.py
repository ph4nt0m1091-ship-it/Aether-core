from permissions.command_policy import CommandPolicy
from permissions.permission_manager import PermissionManager
from providers.local_system_provider import LocalSystemProvider


class TerminalSkill:
    """
    Permission-gated command execution for Aether.
    """

    name = "terminal"

    description = (
        "Runs approved Git, Python, and system commands "
        "with safety checks and user permission."
    )

    def __init__(self, memory):

        self.memory = memory

        self.provider = LocalSystemProvider()

        self.policy = CommandPolicy()

        self.permissions = PermissionManager()

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(self, message):

        message = message.strip()

        # ---------------------------------
        # HANDLE PENDING PERMISSION
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

                command = (
                    pending["data"]
                    .get(
                        "command",
                        ""
                    )
                )

                return self._execute_command(
                    command
                )

            if response == "deny":

                self.permissions.cancel()

                return (
                    "Aether: Command cancelled."
                )

            return (
                "Aether: I am waiting for permission.\n"
                'Say "yes" to approve or "no" to cancel.'
            )

        # ---------------------------------
        # COMMAND REQUEST
        # ---------------------------------

        prefixes = [
            "run command ",
            "run ",
            "execute ",
            "terminal "
        ]

        command = None
        lower = message.lower()

        for prefix in prefixes:

            if lower.startswith(prefix):

                command = message[
                    len(prefix):
                ].strip()

                break

        if command is None:

            return None

        if not command:

            return (
                "Aether: What command "
                "would you like me to run?"
            )

        # ---------------------------------
        # POLICY CHECK
        # ---------------------------------

        policy = self.policy.classify(
            command
        )

        decision = policy.get(
            "decision"
        )

        reason = policy.get(
            "reason",
            ""
        )

        # ---------------------------------
        # BLOCK
        # ---------------------------------

        if decision == "block":

            return (
                "Aether: Command blocked.\n"
                f"Reason: {reason}"
            )

        # ---------------------------------
        # AUTO-ALLOW READ ONLY
        # ---------------------------------

        if decision == "allow":

            return self._execute_command(
                command
            )

        # ---------------------------------
        # REQUIRE CONFIRMATION
        # ---------------------------------

        self.permissions.request(
            "run_command",
            {
                "command": command
            }
        )

        return (
            "Aether: Permission required.\n\n"
            f"Command: {command}\n"
            f"Reason: {reason}\n\n"
            'Say "yes" to approve or "no" to cancel.'
        )

    # ---------------------------------
    # EXECUTE COMMAND
    # ---------------------------------

    def _execute_command(
        self,
        command
    ):

        result = self.provider.execute(
            "run_command",
            {
                "command": command
            }
        )

        if not result.get(
            "success"
        ):

            error = (
                result.get(
                    "stderr"
                )
                or result.get(
                    "error"
                )
                or "Unknown command error."
            )

            return (
                "Aether: Command failed.\n\n"
                f"{error}"
            )

        output = result.get(
            "stdout",
            ""
        )

        if len(output) > 5000:

            output = (
                output[:5000]
                + "\n\n[Output truncated]"
            )

        if not output:

            output = (
                "Command completed successfully."
            )

        return (
            "Aether: Command completed.\n\n"
            f"{output}"
        )

    # ---------------------------------
    # EXECUTE FOR MISSIONS
    # ---------------------------------

    def execute(self, step):

        return None