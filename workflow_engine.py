from providers.aether_provider import AetherProvider
from providers.local_system_provider import LocalSystemProvider
from providers.provider_manager import ProviderManager


class WorkflowEngine:
    """
    Executes dynamic Aether workflows.

    Supports:
    - Aether skills
    - capability providers
    - permission-aware terminal pauses
    """

    def __init__(
        self,
        skill_manager
    ):

        self.skill_manager = skill_manager

        self.providers = ProviderManager()

        self.providers.register(
            AetherProvider()
        )

        self.providers.register(
            LocalSystemProvider()
        )

    # ---------------------------------
    # EXECUTE WORKFLOW
    # ---------------------------------

    def execute(
        self,
        workflow
    ):

        workflow.status = "running"

        while workflow.has_next_step():

            step = workflow.next_step()

            result = self._execute_step(
                step
            )

            # -------------------------
            # PERMISSION PAUSE
            # -------------------------

            if result.get(
                "paused"
            ):

                workflow.status = "paused"

                return {
                    "success": True,
                    "paused": True,
                    "status": "paused",
                    "progress": workflow.progress(),
                    "permission_message": result.get(
                        "response",
                        ""
                    ),
                    "results": workflow.results
                }

            # -------------------------
            # RECORD RESULT
            # -------------------------

            workflow.add_result(
                result
            )

            # -------------------------
            # FAILURE
            # -------------------------

            if not result.get(
                "success",
                False
            ):

                workflow.status = "failed"

                return {
                    "success": False,
                    "paused": False,
                    "status": workflow.status,
                    "progress": workflow.progress(),
                    "results": workflow.results
                }

        workflow.status = "completed"

        return {
            "success": True,
            "paused": False,
            "status": "completed",
            "progress": 100,
            "results": workflow.results
        }

    # ---------------------------------
    # EXECUTE STEP
    # ---------------------------------

    def _execute_step(
        self,
        step
    ):

        step_type = step.get(
            "type"
        )

        action = step.get(
            "action",
            ""
        )

        data = step.get(
            "data",
            {}
        )

        target = step.get(
            "target"
        )

        # ---------------------------------
        # SKILL
        # ---------------------------------

        if step_type == "skill":

            message = data.get(
                "message",
                ""
            )

            response = self.skill_manager.handle(
                message
            )

            if response is None:

                return {
                    "success": False,
                    "type": "skill",
                    "action": action,
                    "error": (
                        "No Aether skill handled "
                        "the workflow request."
                    )
                }

            # -------------------------
            # TERMINAL PERMISSION
            # -------------------------

            if action == "terminal":

                terminal_skill = (
                    self.skill_manager
                    .registry
                    .get_skill(
                        "terminal"
                    )
                )

                if (
                    terminal_skill is not None
                    and terminal_skill.permissions.has_pending()
                ):

                    return {
                        "success": True,
                        "paused": True,
                        "type": "skill",
                        "action": action,
                        "response": response
                    }

            return {
                "success": True,
                "paused": False,
                "type": "skill",
                "action": action,
                "response": response
            }

        # ---------------------------------
        # PROVIDER
        # ---------------------------------

        if step_type == "provider":

            result = self.providers.execute(
                action,
                data,
                provider_name=target
            )

            result["type"] = "provider"
            result["action"] = action
            result["paused"] = False

            return result

        return {
            "success": False,
            "paused": False,
            "type": step_type,
            "action": action,
            "error": (
                f'Unknown workflow step type: '
                f'"{step_type}"'
            )
        }