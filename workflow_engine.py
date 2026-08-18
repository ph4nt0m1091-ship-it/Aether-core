from execution_ledger import ExecutionLedger

from providers.aether_provider import AetherProvider
from providers.local_system_provider import LocalSystemProvider
from providers.provider_manager import ProviderManager

from workflow_store import WorkflowStore


class WorkflowEngine:
    """
    Executes dynamic Aether workflows.

    Supports:
    - Aether skills
    - capability providers
    - structured workflow results
    - workflow field references
    - external AI failure propagation
    - permission-aware terminal pauses
    - persistent workflow state
    - persistent execution history
    """

    def __init__(
        self,
        skill_manager
    ):

        self.skill_manager = (
            skill_manager
        )

        self.providers = (
            ProviderManager()
        )

        self.providers.register(
            AetherProvider()
        )

        self.providers.register(
            LocalSystemProvider()
        )

        self.store = (
            WorkflowStore()
        )

        self.ledger = (
            ExecutionLedger()
        )

    # ---------------------------------
    # EXECUTE WORKFLOW
    # ---------------------------------

    def execute(
        self,
        workflow
    ):

        workflow.status = "running"

        workflow.touch()

        self.store.save(
            workflow
        )

        while workflow.has_next_step():

            step = workflow.next_step()

            self.ledger.record(
                workflow.workflow_id,
                step,
                status="started"
            )

            result = self._execute_step(
                workflow,
                step
            )

            # ---------------------------------
            # PERMISSION PAUSE
            # ---------------------------------

            if result.get(
                "paused"
            ):

                self.ledger.record(
                    workflow.workflow_id,
                    step,
                    result=result,
                    status="paused"
                )

                workflow.rewind_one_step()

                workflow.status = (
                    "paused"
                )

                workflow.touch()

                self.store.save(
                    workflow
                )

                return {
                    "success": True,
                    "paused": True,
                    "status": "paused",
                    "progress": (
                        workflow.progress()
                    ),
                    "permission_message": (
                        result.get(
                            "response",
                            ""
                        )
                    ),
                    "results": (
                        workflow.results
                    )
                }

            workflow.add_result(
                result
            )

            result_status = (
                "completed"
                if result.get(
                    "success",
                    False
                )
                else "failed"
            )

            self.ledger.record(
                workflow.workflow_id,
                step,
                result=result,
                status=result_status
            )

            self.store.save(
                workflow
            )

            if not result.get(
                "success",
                False
            ):

                workflow.status = (
                    "failed"
                )

                workflow.touch()

                self.store.save(
                    workflow
                )

                return {
                    "success": False,
                    "paused": False,
                    "status": "failed",
                    "progress": (
                        workflow.progress()
                    ),
                    "results": (
                        workflow.results
                    )
                }

        workflow.status = "completed"

        workflow.touch()

        self.store.save(
            workflow
        )

        return {
            "success": True,
            "paused": False,
            "status": "completed",
            "progress": 100,
            "results": (
                workflow.results
            )
        }

    # ---------------------------------
    # EXECUTE STEP
    # ---------------------------------

    def _execute_step(
        self,
        workflow,
        step
    ):

        step_type = step.get(
            "type"
        )

        action = step.get(
            "action",
            ""
        )

        raw_data = step.get(
            "data",
            {}
        )

        target = step.get(
            "target"
        )

        # ---------------------------------
        # RESOLVE REFERENCES
        # ---------------------------------

        try:

            data = workflow.resolve_references(
                raw_data
            )

            target = workflow.resolve_references(
                target
            )

        except ValueError as error:

            return {
                "success": False,
                "paused": False,
                "type": step_type,
                "action": action,
                "error": str(
                    error
                )
            }

        # ---------------------------------
        # SKILL
        # ---------------------------------

        if step_type == "skill":

            # ---------------------------------
            # DIRECT STRUCTURED SKILL
            # ---------------------------------

            if "message" not in data:

                skill = (
                    self.skill_manager
                    .registry
                    .get_skill(
                        action
                    )
                )

                if skill is None:

                    return {
                        "success": False,
                        "paused": False,
                        "type": "skill",
                        "action": action,
                        "error": (
                            f'Skill "{action}" '
                            "was not found."
                        )
                    }

                operation = data.get(
                    "operation",
                    ""
                )

                skill_result = (
                    skill.execute(
                        {
                            "action": (
                                operation
                            ),
                            "data": data
                        }
                    )
                )

                if skill_result is None:

                    return {
                        "success": False,
                        "paused": False,
                        "type": "skill",
                        "action": action,
                        "error": (
                            f'Skill "{action}" '
                            "returned no result."
                        )
                    }

                if not isinstance(
                    skill_result,
                    dict
                ):

                    skill_result = {
                        "success": True,
                        "response": str(
                            skill_result
                        )
                    }

                skill_result["type"] = (
                    "skill"
                )

                skill_result["action"] = (
                    action
                )

                skill_result["paused"] = (
                    False
                )

                return skill_result

            # ---------------------------------
            # CONVERSATIONAL SKILL
            # ---------------------------------

            message = data.get(
                "message",
                ""
            )

            response = (
                self.skill_manager
                .handle(
                    message
                )
            )

            if response is None:

                return {
                    "success": False,
                    "paused": False,
                    "type": "skill",
                    "action": action,
                    "error": (
                        "No Aether skill handled "
                        "the workflow request."
                    )
                }

            # ---------------------------------
            # TERMINAL
            # ---------------------------------

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
                    and terminal_skill
                    .permissions
                    .has_pending()
                ):

                    return {
                        "success": True,
                        "paused": True,
                        "type": "skill",
                        "action": action,
                        "response": response
                    }

            # ---------------------------------
            # RESEARCH STRUCTURED RESULT
            # ---------------------------------

            if action == "research":

                research_skill = (
                    self.skill_manager
                    .registry
                    .get_skill(
                        "research"
                    )
                )

                if research_skill is not None:

                    structured = getattr(
                        research_skill,
                        "last_execution_result",
                        None
                    )

                    if structured is not None:

                        if not structured.get(
                            "success",
                            False
                        ):

                            return {
                                "success": False,
                                "paused": False,
                                "type": "skill",
                                "action": action,
                                "response": (
                                    response
                                ),
                                "error": (
                                    structured.get(
                                        "error",
                                        response
                                    )
                                )
                            }

                        return {
                            "success": True,
                            "paused": False,
                            "type": "skill",
                            "action": action,
                            "response": (
                                response
                            ),
                            "query": (
                                structured.get(
                                    "query"
                                )
                            ),
                            "summary": (
                                structured.get(
                                    "summary",
                                    ""
                                )
                            ),
                            "evidence_summary": (
                                structured.get(
                                    "evidence_summary",
                                    ""
                                )
                            ),
                            "shared_topics": (
                                structured.get(
                                    "shared_topics",
                                    []
                                )
                            ),
                            "sources": (
                                structured.get(
                                    "sources",
                                    []
                                )
                            ),
                            "source_count": (
                                structured.get(
                                    "source_count",
                                    0
                                )
                            ),
                            "evidence": (
                                structured.get(
                                    "evidence",
                                    []
                                )
                            )
                        }

            # ---------------------------------
            # PROVIDER STRUCTURED RESULT
            # ---------------------------------

            if action == "providers":

                provider_skill = (
                    self.skill_manager
                    .registry
                    .get_skill(
                        "providers"
                    )
                )

                if provider_skill is not None:

                    provider_result = getattr(
                        provider_skill,
                        "last_execution_result",
                        None
                    )

                    if provider_result is not None:

                        if not provider_result.get(
                            "success",
                            False
                        ):

                            return {
                                "success": False,
                                "paused": False,
                                "type": "skill",
                                "action": action,
                                "response": (
                                    response
                                ),
                                "provider": (
                                    provider_result.get(
                                        "provider"
                                    )
                                ),
                                "error": (
                                    provider_result.get(
                                        "error",
                                        response
                                    )
                                )
                            }

                        answer = (
                            provider_result.get(
                                "response",
                                ""
                            )
                        )

                        return {
                            "success": True,
                            "paused": False,
                            "type": "skill",
                            "action": action,
                            "response": (
                                response
                            ),
                            "answer": answer,
                            "output": answer,
                            "provider": (
                                provider_result.get(
                                    "provider"
                                )
                            ),
                            "model": (
                                provider_result.get(
                                    "model"
                                )
                            ),
                            "capability": (
                                provider_result.get(
                                    "capability"
                                )
                            )
                        }

            # ---------------------------------
            # NORMAL SKILL
            # ---------------------------------

            return {
                "success": True,
                "paused": False,
                "type": "skill",
                "action": action,
                "response": response,
                "output": response
            }

        # ---------------------------------
        # PROVIDER
        # ---------------------------------

        if step_type == "provider":

            result = (
                self.providers.execute(
                    action,
                    data,
                    provider_name=target
                )
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
                f'Unknown workflow '
                f'step type: "{step_type}"'
            )
        }

    # ---------------------------------
    # RECOVERY
    # ---------------------------------

    def latest_unfinished(
        self
    ):

        return (
            self.store
            .latest_unfinished()
        )