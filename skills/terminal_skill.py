from permissions.command_policy import CommandPolicy
from permissions.permission_manager import PermissionManager
from providers.local_system_provider import LocalSystemProvider


class TerminalSkill:
    """
    Permission-gated command execution for Aether.

    Supports both explicit command syntax and a small
    set of natural read-only system requests.
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

    def handle(self, message):

        message = message.strip()

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

        natural_command = (
            self._natural_command(
                message
            )
        )

        if natural_command is not None:

            return (
                self._handle_command(
                    natural_command
                )
            )

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

        return (
            self._handle_command(
                command
            )
        )

    def _natural_command(
        self,
        message
    ):

        lower = (
            str(
                message or ""
            )
            .strip()
            .lower()
            .rstrip("?")
        )

        exact_commands = {
            "show git status": "git status",
            "check git status": "git status",
            "what is the git status": "git status",
            "what's the git status": "git status",
            "show repository status": "git status",
            "show repo status": "git status",
            "check python version": "python --version",
            "show python version": "python --version",
            "what python version do i have": "python --version",
            "what version of python do i have": "python --version",
            "show my ip": "ipconfig",
            "show my ip configuration": "ipconfig",
            "show ip configuration": "ipconfig",
            "show ip config": "ipconfig",
            "check my ip": "ipconfig",
            "check ip configuration": "ipconfig"
        }

        if lower in exact_commands:

            return (
                exact_commands[
                    lower
                ]
            )

        ping_prefixes = (
            "ping ",
            "check connection to ",
            "test connection to "
        )

        for prefix in ping_prefixes:

            if lower.startswith(
                prefix
            ):

                target = (
                    lower[
                        len(prefix):
                    ]
                    .strip()
                )

                if self._safe_ping_target(
                    target
                ):

                    return (
                        "ping "
                        + target
                    )

                return None

        return None

    def _safe_ping_target(
        self,
        target
    ):

        if not target:

            return False

        if len(target) > 253:

            return False

        allowed = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            ".-:"
        )

        return all(
            character in allowed
            for character in target
        )

    def _handle_command(
        self,
        command
    ):

        command = (
            str(
                command or ""
            )
            .strip()
        )

        if not command:

            return (
                "Aether: What command "
                "would you like me to run?"
            )

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

        if decision == "block":

            return (
                "Aether: Command blocked.\n"
                f"Reason: {reason}"
            )

        if decision == "allow":

            return self._execute_command(
                command
            )

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

    def execute(self, step):

        return None
