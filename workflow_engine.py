from providers.aether_provider import AetherProvider
from providers.local_system_provider import LocalSystemProvider
from providers.provider_manager import ProviderManager


class WorkflowEngine:
    """
    Executes dynamic Aether workflows.

    WorkflowEngine can delegate actions to:
    - Aether skills
    - Capability providers

    Terminal commands are intentionally not routed
    directly through providers here because terminal
    commands must remain behind TerminalSkill's
    permission system.
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

        output = []

        while workflow.has_next_step():

            step = workflow.next_step()

            result = self._execute_step(
                step
            )

            workflow.add_result(
                result
            )

            output.append(
                result
            )

            if not result.get(
                "success",
                False
            ):

                workflow.status = "failed"

                return {
                    "success": False,
                    "status": workflow.status,
                    "progress": workflow.progress(),
                    "results": output
                }

        workflow.status = "completed"

        return {
            "success": True,
            "status": workflow.status,
            "progress": 100,
            "results": output
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
        # SKILL MESSAGE
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

            return {
                "success": True,
                "type": "skill",
                "action": action,
                "response": response
            }

        # ---------------------------------
        # PROVIDER CAPABILITY
        # ---------------------------------

        if step_type == "provider":

            result = self.providers.execute(
                action,
                data,
                provider_name=target
            )

            result["type"] = "provider"
            result["action"] = action

            return result

        # ---------------------------------
        # UNKNOWN STEP
        # ---------------------------------

        return {
            "success": False,
            "type": step_type,
            "action": action,
            "error": (
                f'Unknown workflow step type: '
                f'"{step_type}"'
            )
        }