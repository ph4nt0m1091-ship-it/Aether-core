import shlex


class CommandPolicy:
    """
    Safety policy for Aether terminal commands.

    Commands are classified as:

    - allow
    - confirm
    - block

    This is intentionally conservative.
    """

    SAFE_COMMANDS = {
        "git status",
        "git diff",
        "git diff --check",
        "git log",
        "git branch",
        "git rev-parse",
        "python --version",
        "python -v",
        "py --version",
        "where",
        "where.exe",
        "tasklist",
        "ipconfig"
    }

    SAFE_PREFIXES = (
        "git status",
        "git diff",
        "git log",
        "git show",
        "git branch",
        "git rev-parse",
        "git ls-files",
        "python -m py_compile",
        "python --version",
        "python -v",
        "py -m py_compile",
        "where ",
        "where.exe ",
        "tasklist",
        "ipconfig",
        "ping "
    )

    BLOCKED_WORDS = {
        "format",
        "diskpart",
        "bcdedit",
        "shutdown",
        "restart-computer",
        "stop-computer",
        "cipher",
        "takeown"
    }

    BLOCKED_PREFIXES = (
        "del ",
        "erase ",
        "rmdir ",
        "rd ",
        "rm ",
        "remove-item ",
        "reg delete",
        "git clean",
        "git reset --hard"
    )

    def classify(self, command):
        """
        Return policy information for a command.
        """

        command = command.strip()

        if not command:

            return {
                "decision": "block",
                "reason": "No command was provided."
            }

        lower = command.lower()

        if lower.startswith(
            self.BLOCKED_PREFIXES
        ):

            return {
                "decision": "block",
                "reason": (
                    "This command can delete or "
                    "destructively alter data."
                )
            }

        try:

            parts = shlex.split(
                lower,
                posix=False
            )

        except ValueError:

            return {
                "decision": "block",
                "reason": (
                    "The command could not be parsed safely."
                )
            }

        cleaned_parts = [
            part.strip(
                "\"'"
            )
            for part in parts
        ]

        for part in cleaned_parts:

            if part in self.BLOCKED_WORDS:

                return {
                    "decision": "block",
                    "reason": (
                        f'The command contains blocked '
                        f'operation "{part}".'
                    )
                }

        if lower in self.SAFE_COMMANDS:

            return {
                "decision": "allow",
                "reason": "Known read-only command."
            }

        if lower.startswith(
            self.SAFE_PREFIXES
        ):

            return {
                "decision": "allow",
                "reason": "Known read-only command."
            }

        return {
            "decision": "confirm",
            "reason": (
                "This command may modify the system "
                "or project and requires approval."
            )
        }
