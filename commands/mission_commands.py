class MissionCommands:
    """
    Handles goals, plans, and mission progress.
    """

    def handle(self, brain, message):

        message = message.strip()
        lower = message.lower().rstrip("?").strip()

        # ---------------------------------
        # SET GOAL
        # ---------------------------------

        if lower.startswith("set goal "):

            goal = message[len("set goal "):].strip()

            if not goal:
                return (
                    "Aether: Please tell me what the goal is."
                )

            success = brain.cortex.set_goal(goal)

            if not success:
                return (
                    "Aether: I couldn't create that goal."
                )

            return (
                f"Aether: Goal added to Cortex: {goal}"
            )

        # ---------------------------------
        # BUILD GOAL
        # ---------------------------------

        if lower.startswith("build "):

            goal = message[len("build "):].strip()

            if not goal:
                return (
                    "Aether: Please tell me what you want to build."
                )

            success = brain.cortex.set_goal(goal)

            if not success:
                return (
                    "Aether: I couldn't create that goal."
                )

            return (
                f"Aether: Goal added to Cortex: {goal}"
            )

        # ---------------------------------
        # SHOW PLAN
        # ---------------------------------

        if lower == "show plan":

            project = brain.cortex.get_current_project()

            if project is None:
                return (
                    "Aether: No active project. "
                    "Switch to a project first."
                )

            plan = project.get_plan()

            if plan is None:
                return (
                    f'Aether: Project "{project.name}" '
                    "does not have an active plan."
                )

            output = (
                f"Goal: {plan.goal}\n\n"
                "Plan:\n"
            )

            for i, step in enumerate(plan.steps, start=1):

                mark = "✓" if step["completed"] else "□"

                output += (
                    f"{mark} {i}. "
                    f"{step['description']}\n"
                )

            output += (
                f"\nProgress: {plan.progress()}%"
            )

            return output

        # ---------------------------------
        # WHAT'S NEXT
        # ---------------------------------

        if lower in (
            "what's next",
            "whats next",
            "next step",
            "what should i do next"
        ):

            project = brain.cortex.get_current_project()

            if project is None:
                return (
                    "Aether: No active project. "
                    "Switch to a project first."
                )

            plan = project.get_plan()

            if plan is None:
                return (
                    f'Aether: Project "{project.name}" '
                    "does not have an active plan."
                )

            for i, step in enumerate(plan.steps, start=1):

                if not step["completed"]:

                    return (
                        f'Aether: Next step for "{plan.goal}":\n\n'
                        f'{i}. {step["description"]}\n\n'
                        f'Progress: {plan.progress()}%\n\n'
                        f'You can say:\n'
                        f'"complete step {i}"'
                    )

            return (
                f'Aether: All steps for "{plan.goal}" are complete!'
            )

        # ---------------------------------
        # COMPLETE STEP
        # ---------------------------------

        if lower.startswith("complete step"):

            try:

                parts = lower.split()

                if len(parts) < 3:
                    return (
                        "Aether: Please specify which step to complete."
                    )

                index = int(parts[-1]) - 1

                success = brain.cortex.complete_step(index)

                if not success:
                    return (
                        "Aether: I can't complete that step because "
                        "there is no active plan or the step number "
                        "is invalid."
                    )

                return (
                    f"Aether: Step {index + 1} completed."
                )

            except ValueError:

                return (
                    "Aether: Invalid step number."
                )

        return None