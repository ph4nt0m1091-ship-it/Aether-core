class TaskExecutor:
    """
    Executes Tasks one step at a time
    and reports progress to Cortex.
    """

    def __init__(self, skill_manager):

        self.skill_manager = skill_manager

    def execute(self, task, cortex=None):

        print(
            f"\nAether: Starting mission: "
            f"{task.goal}\n"
        )

        # ----------------------------
        # Record Mission Start
        # ----------------------------

        if cortex and cortex.current_project:

            cortex.current_project.add_activity(
                f"Mission started: {task.goal}"
            )

            cortex.projects.save()

        total_steps = len(task)

        # ----------------------------
        # Empty Mission
        # ----------------------------

        if total_steps == 0:

            print(
                "Aether: Mission has no steps."
            )

            if cortex:

                cortex.progress = 100

                if cortex.current_project:

                    cortex.current_project.update_progress(
                        100
                    )

                    cortex.current_project.status = (
                        "Completed"
                    )

                    cortex.current_project.add_activity(
                        f"Mission completed: {task.goal}"
                    )

                    cortex.projects.save()

            print(
                "\nAether: Mission complete."
            )

            return

        # ----------------------------
        # Execute Steps
        # ----------------------------

        while task.has_next_step():

            step = task.next_step()

            skill = step["skill"]
            action = step["action"]

            print(
                f"→ {skill} : {action}"
            )

            self.skill_manager.execute(
                step
            )

            # ----------------------------
            # Record Completed Step
            # ----------------------------

            if cortex and cortex.current_project:

                cortex.current_project.add_activity(
                    f"Mission step completed: "
                    f"{skill} : {action}"
                )

            # ----------------------------
            # Calculate Progress
            # ----------------------------

            completed = task.current_step

            progress = int(
                (completed / total_steps) * 100
            )

            print(
                f"Progress: {progress}%"
            )

            # ----------------------------
            # Update Cortex
            # ----------------------------

            if cortex:

                cortex.progress = progress

                if cortex.current_project:

                    cortex.current_project.update_progress(
                        progress
                    )

                    cortex.projects.save()

        # ----------------------------
        # Mission Complete
        # ----------------------------

        if cortex:

            cortex.progress = 100

            if cortex.current_project:

                cortex.current_project.update_progress(
                    100
                )

                cortex.current_project.status = (
                    "Completed"
                )

                cortex.current_project.add_activity(
                    f"Mission completed: {task.goal}"
                )

                cortex.projects.save()

        print(
            "\nAether: Mission complete."
        )