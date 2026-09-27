import threading

from skills.registry import SkillRegistry


class SkillManager:
    """
    Manages all of Aether's skills.

    A re-entrant lock serializes foreground and
    background skill execution safely.

    Active workflow permission handling receives
    priority so yes/no replies return to the
    workflow that owns the pending action.
    """

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.execution_lock = (
            threading.RLock()
        )

        self.registry = (
            SkillRegistry(
                memory
            )
        )

        self.registry.connect_manager(
            self
        )

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        with self.execution_lock:

            workflow_skill = (
                self.registry
                .get_skill(
                    "workflow"
                )
            )

            if (
                workflow_skill is not None
                and getattr(
                    workflow_skill,
                    "pending_workflow",
                    None
                )
                is not None
            ):

                return (
                    workflow_skill.handle(
                        message
                    )
                )

            return self.registry.handle(
                message
            )

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        with self.execution_lock:

            return self.registry.execute(
                step
            )

    # ---------------------------------
    # SKILLS
    # ---------------------------------

    def available_skills(
        self
    ):

        return (
            self.registry
            .available_skills()
        )

    # ---------------------------------
    # BACKGROUND SERVICES
    # ---------------------------------

    def start_background_services(
        self
    ):

        self.registry.start_background_services()

    def stop_background_services(
        self
    ):

        self.registry.stop_background_services()