from plan import Plan


class PlannerFactory:
    """
    Creates a plan based on the user's goal.
    """

    def create_plan(self, goal):

        goal_lower = goal.lower()

        plan = Plan(goal)

        # ----------------------------
        # Robotics Planning
        # ----------------------------

        if "robot" in goal_lower:

            plan.add_step("Research robotics")
            plan.add_step("Choose hardware")
            plan.add_step("Build prototype")
            plan.add_step("Test prototype")

        # ----------------------------
        # Coding Planning
        # ----------------------------

        elif (
            "code" in goal_lower
            or "program" in goal_lower
            or "software" in goal_lower
        ):

            plan.add_step("Understand the project")
            plan.add_step("Design the architecture")
            plan.add_step("Write the code")
            plan.add_step("Test the program")

        # ----------------------------
        # Generic Planning
        # ----------------------------

        else:

            plan.add_step("Understand the goal")
            plan.add_step("Break the goal into smaller tasks")
            plan.add_step("Start working")
            plan.add_step("Review progress")

        return plan