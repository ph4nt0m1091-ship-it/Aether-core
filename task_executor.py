class TaskExecutor:
    """
    Executes Tasks one step at a time.
    """

    def __init__(self, skill_manager):

        self.skill_manager = skill_manager

    def execute(self, task):

        print(f"\nAether: Starting mission: {task.goal}\n")

        while task.has_next_step():

            step = task.next_step()

            skill = step["skill"]
            action = step["action"]

            print(f"→ {skill} : {action}")

            self.skill_manager.execute(step)

        print("\nAether: Mission complete.")