from goal_orchestrator import GoalOrchestrator
from missions.registry import MissionRegistry


class Planner:
    """
    Aether's planning coordinator.

    Supports both:

    1. Legacy registered missions.
    2. Dynamic natural-language workflow planning.
    """

    def __init__(
        self
    ):

        self.registry = (
            MissionRegistry()
        )

        self.orchestrator = (
            GoalOrchestrator()
        )

    # ---------------------------------
    # LEGACY MISSIONS
    # ---------------------------------

    def create_task(
        self,
        goal
    ):

        mission = (
            self.registry.get(
                goal
            )
        )

        if mission:

            return mission.build()

        return None

    def available_missions(
        self
    ):

        return (
            self.registry
            .list_missions()
        )

    # ---------------------------------
    # DYNAMIC ORCHESTRATION
    # ---------------------------------

    def should_orchestrate(
        self,
        message
    ):

        return (
            self.orchestrator
            .should_orchestrate(
                message
            )
        )

    def create_workflow_request(
        self,
        goal
    ):

        return (
            self.orchestrator
            .build(
                goal
            )
        )