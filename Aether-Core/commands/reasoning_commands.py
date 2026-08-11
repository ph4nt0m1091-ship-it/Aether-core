"""
Reasoning Commands for Aether
Phase 4: Better Reasoning
"""


class ReasoningCommands:
    """
    Handles reasoning-related commands:
    - what should we work on?
    - what's blocking this project?
    - summarize progress
    """

    def handle(self, brain, message):
        """
        Handle reasoning commands.
        Returns a response string or None if not a reasoning command.
        """
        lower = message.lower().strip()

        # ------------------------------
        # 1. What should we work on?
        # ------------------------------
        if lower in (
            "what should we work on",
            "what should we work on?",
            "suggest project",
            "what's next project"
        ):
            return self._suggest_project(brain)

        # ------------------------------
        # 2. What's blocking this project?
        # ------------------------------
        if lower in (
            "what's blocking this project",
            "what's blocking this project?",
            "blocking",
            "what's blocking"
        ):
            return self._check_blockers(brain)

        # ------------------------------
        # 3. Summarize progress
        # ------------------------------
        if lower in (
            "summarize progress",
            "progress summary",
            "summary",
            "show all projects"
        ):
            return self._summarize_progress(brain)

        # Not a reasoning command
        return None

    # ===========================
    # 1. SUGGEST PROJECT
    # ===========================

    def _suggest_project(self, brain):
        """Suggest the most important project to work on."""

        projects = brain.cortex.projects.list_projects()

        if not projects:
            return "Aether: No projects found. Create one with 'switch project <name>'."

        # Calculate priority for each project
        # Priority = (100 - progress) + (1 if active else 0)
        scored = []
        for project in projects:
            progress = project.progress
            priority = (100 - progress)  # Lower progress = higher priority
            scored.append((priority, project))

        # Sort by priority (highest first)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Get the top project
        _, best = scored[0]

        # Build response
        response = f"Aether: I recommend working on \"{best.name}\".\n"
        response += f"Progress: {best.progress}%\n"

        # Get next step if available
        cortex = brain.cortex
        if cortex.current_project == best and cortex.plan:
            steps = cortex.plan.list_steps()
            for i, step in enumerate(steps):
                if not step["completed"]:
                    response += f"Next step: {step['description']}"
                    break
        else:
            response += "Switch to this project to see the plan."

        # List other projects
        if len(projects) > 1:
            response += "\n\nOther projects:"
            for _, project in scored[1:]:
                response += f"\n- {project.name}: {project.progress}% complete"

        return response

    # ===========================
    # 2. CHECK BLOCKERS
    # ===========================

    def _check_blockers(self, brain):
        """Check what's blocking the current project."""

        cortex = brain.cortex
        project = cortex.get_current_project()

        if project is None:
            return "Aether: No active project. Switch to a project first."

        response = f"Aether: Project \"{project.name}\" is {project.progress}% complete.\n"

        if cortex.plan and cortex.plan.steps:
            steps = cortex.plan.list_steps()
            incomplete = [s for s in steps if not s["completed"]]

            if incomplete:
                response += "\nRemaining steps:"
                for i, step in enumerate(incomplete, 1):
                    response += f"\n{i}. {step['description']}"

                response += "\n\nNo blocks detected. All dependencies are available."
            else:
                response += "\nAll steps are complete! Time to celebrate 🎉"
        else:
            response += "\nNo plan found for this project. Create one with 'set goal <goal>'."

        return response

    # ===========================
    # 3. SUMMARIZE PROGRESS
    # ===========================

    def _summarize_progress(self, brain):
        """Summarize all projects."""

        projects = brain.cortex.projects.list_projects()

        if not projects:
            return "Aether: No projects found. Create one with 'switch project <name>'."

        response = "Aether: Active Projects:\n"

        # Track total progress
        total = 0
        for project in projects:
            # Get next step
            next_step = "No plan"
            if project == brain.cortex.current_project and brain.cortex.plan:
                steps = brain.cortex.plan.list_steps()
                for step in steps:
                    if not step["completed"]:
                        next_step = step["description"]
                        break
                else:
                    next_step = "Complete!"
            else:
                next_step = "Switch to see plan"

            response += f"\n{project.name} - {project.progress}% complete (next: {next_step})"

            total += project.progress

        avg_progress = int(total / len(projects)) if projects else 0
        response += f"\n\nTotal progress across all projects: {avg_progress}%"

        return response