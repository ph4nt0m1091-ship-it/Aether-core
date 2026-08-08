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

                return (
                    "Aether: I don't currently have any missions."
                )

            return (
                "Aether: I currently know these missions:\n\n- "
                + "\n- ".join(missions)
            )

        # ----------------------------
        # Run Mission
        # ----------------------------

        if lower.startswith("run mission "):

            goal = message[len("run mission "):].strip()

            if not goal:

                return "Aether: Please provide a mission."

            task = brain.planner.create_task(goal)

            if task is None:

                return (
                    f'Aether: I don\'t know how to run '
                    f'the mission "{goal}".'
                )

            brain.executor.execute(task)

            return "Aether: Mission finished."

        return None