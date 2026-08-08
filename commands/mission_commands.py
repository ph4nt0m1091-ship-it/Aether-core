class MissionCommands:
    """
    Handles mission-related commands.
    """

    def handle(self, brain, message):

        lower = message.lower().rstrip("?")

        # ----------------------------
        # Show Available Missions
        # ----------------------------

        if lower in (
            "what missions do you know",
            "what missions do you have",
            "list missions",
            "show missions"
        ):

            missions = brain.planner.available_missions()

            if not missions:

                return "Aether: I don't currently have any missions."

            return (
                "Aether: I currently know these missions:\n\n- "
                + "\n- ".join(missions)
            )

        # ----------------------------
        # Run Mission
        # ----------------------------

        if lower.startswith("run mission "):

            mission_name = message[len("run mission "):].strip()

            if not mission_name:

                return "Aether: Please provide a mission."

            # Find the mission task
            task = brain.planner.create_task(mission_name)

            if task is None:

                return (
                    f'Aether: I don\'t know how to run '
                    f'the mission "{mission_name}".'
                )

            # ----------------------------
            # Create / activate project
            # ----------------------------

            project_name = mission_name

            if mission_name.lower() == "start robotics project":

                project_name = "robotics"

            project = brain.cortex.projects.create_project(
                project_name
            )

            brain.cortex.current_project = project

            project.set_goal(mission_name)

            project.status = "Active"

            brain.cortex.projects.save()

            # ----------------------------
            # Execute mission
            # ----------------------------

            brain.executor.execute(task, brain.cortex)

            return (
                f'Aether: Mission "{mission_name}" finished.\n'
                f'Project "{project.name}" is now active.'
            )

        return None