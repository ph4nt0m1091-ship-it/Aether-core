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

            output += (
                f'Goal: '
                f'{project.goal or "None"}\n'
            )

            output += (
                f'Status: '
                f'{project.status}\n'
            )

            output += (
                f'Progress: '
                f'{project.progress}%\n'
            )

            output += (
                f'Notes: '
                f'{len(notes)}\n'
            )

            output += (
                f'Activity: '
                f'{len(activity)} events\n'
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
        # What's Next
        # ----------------------------

        if lower in (
            "what's next",
            "whats next",
            "what is next",
            "next step",
            "what should i do next"
        ):

            project = brain.cortex.get_current_project()

            if project is None:

                return "Aether: No active project."

            plan = brain.cortex.get_plan()

            if plan is None:

                return (
                    f'Aether: Project "{project.name}" '
                    f'does not have an active plan.'
                )

            steps = plan.list_steps()

            if not steps:

                return (
                    f'Aether: Project "{project.name}" '
                    f'does not have any planned steps.'
                )

            # ----------------------------
            # Find First Incomplete Step
            # ----------------------------

            next_step = None
            next_index = None

            for index, step in enumerate(
                steps,
                start=1
            ):

                if not step["completed"]:

                    next_step = step
                    next_index = index
                    break

            # ----------------------------
            # No Remaining Steps
            # ----------------------------

            if next_step is None:

                return (
                    f'Aether: There are no remaining '
                    f'steps for "{project.name}".\n\n'
                    f'Progress: {project.progress}%\n'
                    f'Project is complete.'
                )

            # ----------------------------
            # Remaining Step
            # ----------------------------

            return (
                f'Aether: Next step for '
                f'"{project.name}":\n\n'
                f'{next_index}. '
                f'{next_step["description"]}\n\n'
                f'Progress: {project.progress}%\n\n'
                f'You can say:\n'
                f'"complete step {next_index}"'
            )

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