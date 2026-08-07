class ProjectCommands:
    """
    Handles project-related commands.
    """

    def handle(self, brain, message):

        lower = message.lower().rstrip("?")

        # ----------------------------
        # Current Project
        # ----------------------------

        if lower in (

            "current project",

            "show current project"

        ):

            project = brain.cortex.get_current_project()

            if project is None:

                return "Aether: No active project."

            return (
                f'Aether: Current project is "{project.name}".'
            )

        # ----------------------------
        # Switch Project
        # ----------------------------

        if lower.startswith("switch project "):

            name = message[len("switch project "):].strip()

            if brain.cortex.switch_project(name):

                return (
                    f'Aether: Current project set to "{name}".'
                )

            return "Aether: Project not found."

        return None