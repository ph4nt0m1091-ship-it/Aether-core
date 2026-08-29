from execution_ledger import ExecutionLedger
from resilience import ResiliencePolicy

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
    - terminal permission pauses
    - external-agent permission pauses
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

        self.resilience = (
            ResiliencePolicy()
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

            result = self._execute_with_recovery(
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
                    "failed_step": (
                        workflow.current_step
                    ),
                    "failure_type": (
                        result.get(
                            "failure_type",
                            "unknown"
                        )
                    ),
                    "recovery": (
                        result.get(
                            "recovery",
                            {}
                        )
                    ),
                    "error": (
                        result.get(
                            "error",
                            "Unknown workflow error."
                        )
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
    # SAFE FAILURE RECOVERY
    # ---------------------------------

    def _retry_capability(
        self,
        step,
        result
    ):
        """
        Return the conservative capability name used
        by ResiliencePolicy.

        Only read-only/provider-generation operations
        are eligible for automatic retries. Permission
        pauses and state-changing operations never reach
        the retry path.
        """

        step_type = step.get(
            "type",
            ""
        )

        action = step.get(
            "action",
            ""
        )

        if step_type == "provider":
            return action

        if step_type != "skill":
            return None

        if action == "providers":
            return (
                result.get(
                    "capability"
                )
                or "generate_text"
            )

        if action == "research":
            return "research"

        if action == "web_search":
            return "web_search"

        return None

    def _build_fallback_step(
        self,
        step,
        model
    ):
        """
        Create a copy of a direct local provider step with
        only its approved model changed.
        """

        fallback_step = dict(
            step
        )

        original_data = step.get(
            "data",
            {}
        )

        fallback_data = dict(
            original_data
            if isinstance(
                original_data,
                dict
            )
            else {}
        )

        fallback_data[
            "model"
        ] = model

        fallback_step[
            "data"
        ] = fallback_data

        return fallback_step

    def _attempt_safe_fallback(
        self,
        workflow,
        step,
        retry_result,
        recovery
    ):
        """
        Try deterministic fallback candidates after the
        original attempt and one safe retry have failed.

        Only ResiliencePolicy-approved fallback plans are
        accepted. Each fallback attempt is recorded in the
        execution ledger. Permission pauses are returned
        immediately and never bypassed.
        """

        plan = (
            self.resilience.fallback_plan(
                step,
                retry_result
            )
        )

        if plan is None:

            recovery[
                "fallback_attempted"
            ] = False

            return (
                retry_result,
                recovery
            )

        candidates = list(
            plan.get(
                "candidates",
                []
            )
        )

        recovery[
            "fallback_attempted"
        ] = bool(
            candidates
        )

        recovery[
            "fallback_provider"
        ] = plan.get(
            "provider"
        )

        recovery[
            "fallback_from_model"
        ] = plan.get(
            "from_model"
        )

        recovery[
            "fallback_candidates"
        ] = candidates

        recovery[
            "fallback_succeeded"
        ] = False

        recovery[
            "fallback_model"
        ] = None

        recovery[
            "fallback_errors"
        ] = []

        for model in candidates:

            fallback_step = (
                self._build_fallback_step(
                    step,
                    model
                )
            )

            self.ledger.record(
                workflow.workflow_id,
                fallback_step,
                status="fallback_started"
            )

            fallback_result = (
                self._execute_step(
                    workflow,
                    fallback_step
                )
            )

            if fallback_result.get(
                "paused"
            ):

                recovery[
                    "fallback_model"
                ] = model

                recovery[
                    "fallback_pause"
                ] = True

                fallback_result[
                    "recovery"
                ] = recovery

                return (
                    fallback_result,
                    recovery
                )

            if fallback_result.get(
                "success",
                False
            ):

                recovery[
                    "fallback_succeeded"
                ] = True

                recovery[
                    "fallback_model"
                ] = model

                fallback_result[
                    "failure_type"
                ] = "success"

                fallback_result[
                    "recovery"
                ] = recovery

                self.ledger.record(
                    workflow.workflow_id,
                    fallback_step,
                    result=fallback_result,
                    status="fallback_completed"
                )

                return (
                    fallback_result,
                    recovery
                )

            fallback_error = (
                fallback_result.get(
                    "error",
                    "Unknown fallback error."
                )
            )

            recovery[
                "fallback_errors"
            ].append(
                {
                    "model": model,
                    "error": fallback_error,
                    "failure_type": (
                        self.resilience.classify(
                            fallback_result
                        )
                    )
                }
            )

            self.ledger.record(
                workflow.workflow_id,
                fallback_step,
                result=fallback_result,
                status="fallback_failed"
            )

        retry_result[
            "recovery"
        ] = recovery

        return (
            retry_result,
            recovery
        )

    def _execute_with_recovery(
        self,
        workflow,
        step
    ):
        """
        Execute one workflow step with conservative
        recovery:

        1. Run the original step.
        2. Retry it once only when the shared policy says
           that retry is safe.
        3. If that retry still fails, optionally try an
           explicitly approved deterministic fallback.
        4. Never bypass a permission pause or silently
           move a local request to cloud.
        """

        first_result = self._execute_step(
            workflow,
            step
        )

        if first_result.get(
            "paused"
        ):
            return first_result

        if first_result.get(
            "success",
            False
        ):
            return first_result

        failure_type = (
            self.resilience.classify(
                first_result
            )
        )

        first_result[
            "failure_type"
        ] = failure_type

        capability = (
            self._retry_capability(
                step,
                first_result
            )
        )

        can_retry = (
            capability is not None
            and self.resilience.can_retry(
                capability,
                first_result
            )
        )

        if not can_retry:

            first_result[
                "recovery"
            ] = {
                "attempted": False,
                "attempts": 1,
                "retry_succeeded": False,
                "capability": capability,
                "failure_type": failure_type,
                "fallback_attempted": False
            }

            return first_result

        self.ledger.record(
            workflow.workflow_id,
            step,
            result=first_result,
            status="failed"
        )

        retry_result = self._execute_step(
            workflow,
            step
        )

        recovery = {
            "attempted": True,
            "attempts": 2,
            "retry_succeeded": False,
            "capability": capability,
            "failure_type": failure_type,
            "initial_error": (
                first_result.get(
                    "error",
                    ""
                )
            ),
            "retry_error": None,
            "fallback_attempted": False
        }

        if retry_result.get(
            "paused"
        ):

            retry_result[
                "recovery"
            ] = recovery

            return retry_result

        retry_succeeded = bool(
            retry_result.get(
                "success",
                False
            )
        )

        recovery[
            "retry_succeeded"
        ] = retry_succeeded

        recovery[
            "retry_error"
        ] = (
            None
            if retry_succeeded
            else retry_result.get(
                "error",
                ""
            )
        )

        if retry_succeeded:

            retry_result[
                "failure_type"
            ] = "success"

            retry_result[
                "recovery"
            ] = recovery

            return retry_result

        retry_result[
            "failure_type"
        ] = (
            self.resilience.classify(
                retry_result
            )
        )

        fallback_result, recovery = (
            self._attempt_safe_fallback(
                workflow,
                step,
                retry_result,
                recovery
            )
        )

        fallback_result[
            "recovery"
        ] = recovery

        return fallback_result

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
            # TERMINAL PERMISSION
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
                        "permission_source": (
                            "terminal"
                        ),
                        "response": response
                    }

            # ---------------------------------
            # PROVIDER PERMISSION
            # ---------------------------------

            if action == "providers":

                provider_skill = (
                    self.skill_manager
                    .registry
                    .get_skill(
                        "providers"
                    )
                )

                if (
                    provider_skill is not None
                    and provider_skill
                    .permissions
                    .has_pending()
                ):

                    return {
                        "success": True,
                        "paused": True,
                        "type": "skill",
                        "action": action,
                        "permission_source": (
                            "providers"
                        ),
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
                                "provider_type": (
                                    provider_result.get(
                                        "provider_type"
                                    )
                                ),
                                "capability": (
                                    provider_result.get(
                                        "capability"
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
                            or provider_result.get(
                                "stdout",
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
                            "provider_type": (
                                provider_result.get(
                                    "provider_type"
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
                            ),
                            "returncode": (
                                provider_result.get(
                                    "returncode"
                                )
                            ),
                            "stdout": (
                                provider_result.get(
                                    "stdout"
                                )
                            ),
                            "stderr": (
                                provider_result.get(
                                    "stderr"
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
