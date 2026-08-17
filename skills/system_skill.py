from providers.local_system_provider import LocalSystemProvider


class SystemSkill:
    """
    Gives Aether controlled access to local Windows actions.

    Current abilities:
    - Open approved applications
    - Open existing files and folders
    - Show running processes
    """

    name = "system"

    description = (
        "Opens approved applications, opens files or folders, "
        "and inspects running Windows processes."
    )

    def __init__(self, memory):

        self.memory = memory
        self.provider = LocalSystemProvider()

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(self, message):

        message = message.strip()
        lower = message.lower()

        # ---------------------------------
        # SHOW RUNNING PROCESSES
        # ---------------------------------

        if lower in (
            "show running processes",
            "show processes",
            "list processes",
            "what is running",
            "what's running",
            "whats running"
        ):

            result = self.provider.execute(
                "list_processes",
                {}
            )

            if not result.get(
                "success"
            ):

                return (
                    "Aether: I couldn't read the "
                    "running processes."
                )

            processes = result.get(
                "processes",
                []
            )

            output = (
                f"Aether: I found "
                f"{len(processes)} running processes.\n\n"
            )

            for process in processes[:20]:

                output += (
                    f"- {process.get('name', 'Unknown')} "
                    f"(PID {process.get('pid', '?')})\n"
                )

            if len(processes) > 20:

                output += (
                    f"\nShowing the first 20 of "
                    f"{len(processes)} processes."
                )

            return output.rstrip()

        # ---------------------------------
        # OPEN APPLICATION
        # ---------------------------------

        if lower.startswith(
            "open "
        ):

            target = message[
                len("open "):
            ].strip()

            if not target:

                return (
                    "Aether: What would you "
                    "like me to open?"
                )

            # Try an approved application first.
            app_result = self.provider.execute(
                "open_app",
                {
                    "app": target
                }
            )

            if app_result.get(
                "success"
            ):

                return (
                    f"Aether: Opening {target}."
                )

            # If it isn't an approved app,
            # try treating it as a file/folder path.
            path_result = self.provider.execute(
                "open_path",
                {
                    "path": target
                }
            )

            if path_result.get(
                "success"
            ):

                return (
                    f"Aether: Opening {target}."
                )

            return (
                f'Aether: I could not open "{target}".\n'
                "It may not be an approved application "
                "or an existing file/folder path."
            )

        return None

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(self, step):
        """
        Allows missions to use system capabilities later.
        """

        capability = step.get(
            "action"
        )

        data = step.get(
            "data",
            {}
        )

        return self.provider.execute(
            capability,
            data
        )