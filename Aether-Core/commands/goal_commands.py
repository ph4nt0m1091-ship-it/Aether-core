class GoalCommands:
    """
    Handles goal and planning commands.
    """

    def handle(self, brain, message):

        lower = message.lower().rstrip("?")

        # ----------------------------
        # Build Goal
        # ----------------------------

        if lower.startswith("build "):

            goal = message[6:].strip()

            brain.cortex.set_goal(goal)

            return "Aether: Goal added to Cortex."

        # ----------------------------
        # Show Plan
        # ----------------------------

        if lower == "show plan":

            plan = brain.cortex.get_plan()

            if plan is None:

                return "Aether: No active plan."

            output = (
                f"Goal: {brain.cortex.get_goal()}\n\n"
                "Plan:\n"
            )

            for i, step in enumerate(plan.steps, start=1):

                mark = "✓" if step["completed"] else "□"

                output += (
                    f"{mark} {i}. "
                    f"{step['description']}\n"
                )

            output += (
                f"\nProgress: "
                f"{brain.cortex.get_progress()}%"
            )

            return output

        # ----------------------------
        # Complete Step
        # ----------------------------

        if lower.startswith("complete step"):

            try:

                index = int(lower.split()[-1]) - 1

                brain.cortex.complete_step(index)

                return "Aether: Step completed."

            except Exception:

                return "Aether: Invalid step."

        return None