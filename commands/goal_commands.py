class GoalCommands:
    """
    Handles goal and planning commands.
    """

    def handle(self, brain, message):

        lower = message.lower().strip().rstrip("?")

        # ----------------------------
        # Build Goal
        # ----------------------------

        if lower.startswith("build "):

            goal = message[6:].strip()

            if not goal:
                return "Aether: Please tell me what you want to build."

            brain.cortex.set_goal(goal)

            return f"Aether: Goal added to Cortex: {goal}"

        # ----------------------------
        # Set Goal
        # ----------------------------

        if lower.startswith("set goal "):

            goal = message[9:].strip()

            if not goal:
                return "Aether: Please tell me what the goal should be."

            brain.cortex.set_goal(goal)

            return f"Aether: Goal added to Cortex: {goal}"

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