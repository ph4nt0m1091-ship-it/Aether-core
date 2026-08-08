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
        # Project Status
        # ----------------------------

        if lower in (
            "project status",
            "show project status",
            "status of project"
        ):

            project = brain.cortex.get_current_project()

            if project is None:

                return "Aether: No active project."

            activity = project.get_activity()

            notes = project.get_notes()

            output = (
                f'Aether: Project Status — '
                f'{project.name}\n\n'
                f'Goal: {project.goal or "None"}\n'
                f'Status: {project.status}\n'
                f'Progress: {project.progress}%\n'
                f'Notes: {len(notes)}\n'
                f'Activity: {len(activity)} events'
            )

            if activity:

                last_event = activity[-1]

                if isinstance(last_event, dict):

                    timestamp = last_event.get(
                        "timestamp",
                        "Unknown"
                    )

                    event_message = last_event.get(
                        "message",
                        ""
                    )

                    output += (
                        f'\n\nLast activity:\n'
                        f'[{timestamp}] '
                        f'{event_message}'
                    )

                else:

                    output += (
                        f'\n\nLast activity:\n'
                        f'[Unknown] {last_event}'
                    )

            return output

                # ----------------------------
        # Project Summary
        # ----------------------------

        if lower in (
            "summarize project",
            "project summary",
            "summary of project",
            "summarize this project"
        ):

            project = brain.cortex.get_current_project()

            if project is None:

                return "Aether: No active project."

            notes = project.get_notes()
            activity = project.get_activity()

            output = (
                f'Aether: Project Summary — '
                f'{project.name}\n\n'
            )

            # ----------------------------
            # Goal
            # ----------------------------

            output += (
                f'Goal: '
                f'{project.goal or "None"}\n'
            )

            # ----------------------------
            # Status
            # ----------------------------

            output += (
                f'Status: '
                f'{project.status}\n'
            )

            # ----------------------------
            # Progress
            # ----------------------------

            output += (
                f'Progress: '
                f'{project.progress}%\n'
            )

            # ----------------------------
            # Notes
            # ----------------------------

            output += (
                f'Notes: '
                f'{len(notes)}\n'
            )

            # ----------------------------
            # Activity
            # ----------------------------

            output += (
                f'Activity: '
                f'{len(activity)} events\n'
            )

            # ----------------------------
            # Last Activity
            # ----------------------------

            if activity:

                last_event = activity[-1]

                if isinstance(last_event, dict):

                    timestamp = last_event.get(
                        "timestamp",
                        "Unknown"
                    )

                    event_message = last_event.get(
                        "message",
                        ""
                    )

                    output += (
                        f'\nLast activity:\n'
                        f'[{timestamp}] '
                        f'{event_message}\n'
                    )

                else:

                    output += (
                        f'\nLast activity:\n'
                        f'[Unknown] '
                        f'{last_event}\n'
                    )

            # ----------------------------
            # Completion Message
            # ----------------------------

            if project.progress >= 100:

                output += (
                    '\nProject is complete.'
                )

            elif project.progress > 0:

                output += (
                    '\nProject is currently in progress.'
                )

            else:

                output += (
                    '\nProject has not started yet.'
                )

            return output

        # ----------------------------
        # Switch Project
        # ----------------------------

        if lower.startswith("switch project "):

            name = message[
                len("switch project "):
            ].strip()

            if not name:

                return (
                    "Aether: Please provide "
                    "a project name."
                )

            if brain.cortex.switch_project(name):

                return (
                    f'Aether: Current project set '
                    f'to "{name.lower()}".'
                )

            return "Aether: Project not found."

        return None