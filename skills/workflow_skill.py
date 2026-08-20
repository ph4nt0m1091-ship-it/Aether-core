import re

from workflow import Workflow
from workflow_engine import WorkflowEngine


class WorkflowSkill:
    """
    Coordinates persistent, resumable Aether workflows.

    Workflows can:
    - Execute multiple skills/providers
    - Use external AI providers
    - Use permission-gated external agents
    - Pass structured data between workflow steps
    - Reference previous or specific step results
    - Save workflow results to files
    - Pause for terminal permission
    - Pause for external-agent permission
    - Resume after approval
    - Survive Aether restarts
    - Recover unfinished work safely

    Permission itself is never persisted.
    """

    name = "workflow"

    description = (
        "Coordinates persistent multi-step Aether workflows "
        "with structured data passing, external providers, "
        "permissions, persistence, and recovery."
    )

    def __init__(
        self,
        memory,
        skill_manager=None
    ):

        self.memory = memory
        self.skill_manager = skill_manager

        self.engine = None

        self.pending_workflow = None
        self.recovered_workflow = None

    # ---------------------------------
    # CONNECT MANAGER
    # ---------------------------------

    def connect(
        self,
        skill_manager
    ):

        self.skill_manager = skill_manager

        self.engine = WorkflowEngine(
            skill_manager
        )

        self.recovered_workflow = (
            self.engine.latest_unfinished()
        )

        if (
            self.recovered_workflow is not None
            and self.recovered_workflow.status
            == "running"
        ):

            self.recovered_workflow.status = (
                "paused"
            )

            self.recovered_workflow.touch()

            self.engine.store.save(
                self.recovered_workflow
            )

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        message = message.strip()
        lower = message.lower()

        # ---------------------------------
        # ACTIVE PERMISSION REQUEST
        # ---------------------------------

        if self.pending_workflow is not None:

            return (
                self._handle_pending_workflow(
                    message
                )
            )

        # ---------------------------------
        # WORKFLOW STATUS
        # ---------------------------------

        if lower in (
            "workflow status",
            "show workflow",
            "show current workflow",
            "show pending workflow"
        ):

            return self._workflow_status()

        # ---------------------------------
        # RESUME WORKFLOW
        # ---------------------------------

        if lower in (
            "resume workflow",
            "resume last workflow",
            "continue workflow",
            "continue last workflow"
        ):

            return (
                self._resume_saved_workflow()
            )

        # ---------------------------------
        # CANCEL WORKFLOW
        # ---------------------------------

        if lower in (
            "cancel workflow",
            "cancel current workflow"
        ):

            return (
                self._cancel_saved_workflow()
            )

        # ---------------------------------
        # NEW WORKFLOW
        # ---------------------------------

        if not lower.startswith(
            "workflow "
        ):

            return None

        if self.engine is None:

            return (
                "Aether: Workflow Engine "
                "is not connected."
            )

        request = message[
            len("workflow "):
        ].strip()

        if not request:

            return (
                "Aether: What would you "
                "like the workflow to do?"
            )

        workflow = (
            self._build_workflow(
                request
            )
        )

        if len(workflow) == 0:

            return (
                "Aether: I couldn't build "
                "a workflow from that request."
            )

        result = (
            self.engine.execute(
                workflow
            )
        )

        if result.get(
            "paused"
        ):

            self.pending_workflow = (
                workflow
            )

            self.recovered_workflow = (
                workflow
            )

        elif workflow.status in (
            "completed",
            "failed",
            "cancelled"
        ):

            self.recovered_workflow = None

        return (
            self._format_result(
                workflow,
                result
            )
        )

    # ---------------------------------
    # RESUME PERSISTED WORKFLOW
    # ---------------------------------

    def _resume_saved_workflow(
        self
    ):

        if self.engine is None:

            return (
                "Aether: Workflow Engine "
                "is not connected."
            )

        workflow = (
            self.recovered_workflow
        )

        if workflow is None:

            workflow = (
                self.engine
                .latest_unfinished()
            )

        if workflow is None:

            return (
                "Aether: There is no unfinished "
                "workflow to resume."
            )

        self.recovered_workflow = (
            workflow
        )

        result = (
            self.engine.execute(
                workflow
            )
        )

        if result.get(
            "paused"
        ):

            self.pending_workflow = (
                workflow
            )

        elif workflow.status in (
            "completed",
            "failed",
            "cancelled"
        ):

            self.recovered_workflow = None

        return (
            self._format_result(
                workflow,
                result
            )
        )

    # ---------------------------------
    # FIND PENDING PERMISSION SKILL
    # ---------------------------------

    def _pending_permission_skill(
        self
    ):

        terminal_skill = (
            self.skill_manager
            .registry
            .get_skill(
                "terminal"
            )
        )

        provider_skill = (
            self.skill_manager
            .registry
            .get_skill(
                "providers"
            )
        )

        if (
            terminal_skill is not None
            and terminal_skill
            .permissions
            .has_pending()
        ):

            return (
                "terminal",
                terminal_skill
            )

        if (
            provider_skill is not None
            and provider_skill
            .permissions
            .has_pending()
        ):

            return (
                "providers",
                provider_skill
            )

        return (
            None,
            None
        )

    # ---------------------------------
    # HANDLE PAUSED PERMISSION
    # ---------------------------------

    def _handle_pending_workflow(
        self,
        message
    ):

        permission_source, skill = (
            self._pending_permission_skill()
        )

        workflow = (
            self.pending_workflow
        )

        if skill is None:

            workflow.status = (
                "paused"
            )

            workflow.touch()

            self.engine.store.save(
                workflow
            )

            self.pending_workflow = None
            self.recovered_workflow = (
                workflow
            )

            return (
                "Aether: The workflow permission "
                "request is no longer active.\n"
                "Use \"resume workflow\" to recreate "
                "the permission request safely."
            )

        permission_response = (
            skill.handle(
                message
            )
        )

        if (
            skill.permissions
            .has_pending()
        ):

            return (
                permission_response
            )

        # ---------------------------------
        # USER DENIED
        # ---------------------------------

        denied = False

        if permission_source == "terminal":

            denied = (
                permission_response
                == "Aether: Command cancelled."
            )

        elif permission_source == "providers":

            denied = (
                permission_response
                == (
                    "Aether: External agent "
                    "execution cancelled."
                )
            )

        if denied:

            workflow.status = (
                "cancelled"
            )

            workflow.touch()

            self.engine.store.save(
                workflow
            )

            self.pending_workflow = None
            self.recovered_workflow = None

            return (
                f"{permission_response}\n\n"
                "Aether: Workflow cancelled.\n"
                f"Progress: "
                f"{workflow.progress()}%"
            )

        # ---------------------------------
        # ADVANCE PAST APPROVED STEP
        # ---------------------------------

        if workflow.has_next_step():

            workflow.current_step += 1

            workflow.touch()

        # ---------------------------------
        # TERMINAL RESULT
        # ---------------------------------

        if permission_source == "terminal":

            if (
                permission_response
                .startswith(
                    "Aether: Command failed."
                )
            ):

                workflow.add_result(
                    {
                        "success": False,
                        "paused": False,
                        "type": "skill",
                        "action": "terminal",
                        "response": (
                            permission_response
                        ),
                        "error": (
                            permission_response
                        )
                    }
                )

                workflow.status = (
                    "failed"
                )

                workflow.touch()

                self.engine.store.save(
                    workflow
                )

                self.pending_workflow = None
                self.recovered_workflow = None

                return (
                    self._format_result(
                        workflow,
                        {
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
                    )
                )

            workflow.add_result(
                {
                    "success": True,
                    "paused": False,
                    "type": "skill",
                    "action": "terminal",
                    "response": (
                        permission_response
                    ),
                    "output": (
                        permission_response
                    )
                }
            )

        # ---------------------------------
        # EXTERNAL PROVIDER RESULT
        # ---------------------------------

        elif permission_source == "providers":

            provider_result = getattr(
                skill,
                "last_execution_result",
                None
            )

            if (
                provider_result is None
                or not provider_result.get(
                    "success",
                    False
                )
            ):

                error = (
                    provider_result.get(
                        "error"
                    )
                    if isinstance(
                        provider_result,
                        dict
                    )
                    else permission_response
                )

                workflow.add_result(
                    {
                        "success": False,
                        "paused": False,
                        "type": "skill",
                        "action": "providers",
                        "response": (
                            permission_response
                        ),
                        "provider": (
                            provider_result.get(
                                "provider"
                            )
                            if isinstance(
                                provider_result,
                                dict
                            )
                            else None
                        ),
                        "error": (
                            error
                            or permission_response
                        )
                    }
                )

                workflow.status = (
                    "failed"
                )

                workflow.touch()

                self.engine.store.save(
                    workflow
                )

                self.pending_workflow = None
                self.recovered_workflow = None

                return (
                    self._format_result(
                        workflow,
                        {
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
                    )
                )

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

            workflow.add_result(
                {
                    "success": True,
                    "paused": False,
                    "type": "skill",
                    "action": "providers",
                    "response": (
                        permission_response
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
            )

        self.engine.store.save(
            workflow
        )

        self.pending_workflow = None

        result = (
            self.engine.execute(
                workflow
            )
        )

        if result.get(
            "paused"
        ):

            self.pending_workflow = (
                workflow
            )

            self.recovered_workflow = (
                workflow
            )

        elif workflow.status in (
            "completed",
            "failed",
            "cancelled"
        ):

            self.recovered_workflow = None

        return (
            self._format_result(
                workflow,
                result
            )
        )

    # ---------------------------------
    # WORKFLOW STATUS
    # ---------------------------------

    def _workflow_status(
        self
    ):

        workflow = (
            self.pending_workflow
            or self.recovered_workflow
        )

        if workflow is None:

            workflow = (
                self.engine
                .latest_unfinished()
            )

        if workflow is None:

            return (
                "Aether: No unfinished "
                "workflow found."
            )

        next_step = (
            workflow.peek_next_step()
        )

        output = (
            "Aether: Current Workflow\n\n"
            f"ID: {workflow.workflow_id}\n"
            f"Goal: {workflow.goal}\n"
            f"Status: {workflow.status}\n"
            f"Progress: "
            f"{workflow.progress()}%\n"
            f"Completed results: "
            f"{len(workflow.results)}"
        )

        if next_step:

            output += (
                "\n\nNext step:\n"
                f"- Type: "
                f"{next_step.get('type')}\n"
                f"- Action: "
                f"{next_step.get('action')}"
            )

        return output

    # ---------------------------------
    # CANCEL SAVED WORKFLOW
    # ---------------------------------

    def _cancel_saved_workflow(
        self
    ):

        workflow = (
            self.pending_workflow
            or self.recovered_workflow
        )

        if workflow is None:

            workflow = (
                self.engine
                .latest_unfinished()
            )

        if workflow is None:

            return (
                "Aether: There is no unfinished "
                "workflow to cancel."
            )

        terminal_skill = (
            self.skill_manager
            .registry
            .get_skill(
                "terminal"
            )
        )

        provider_skill = (
            self.skill_manager
            .registry
            .get_skill(
                "providers"
            )
        )

        if terminal_skill is not None:

            terminal_skill.permissions.cancel()

        if provider_skill is not None:

            provider_skill.permissions.cancel()

        workflow.status = (
            "cancelled"
        )

        workflow.touch()

        self.engine.store.save(
            workflow
        )

        self.pending_workflow = None
        self.recovered_workflow = None

        return (
            "Aether: Workflow cancelled.\n"
            f"ID: {workflow.workflow_id}"
        )

    # ---------------------------------
    # NORMALIZE RESULT REFERENCES
    # ---------------------------------

    def _normalize_references(
        self,
        text
    ):

        text = re.sub(
            r"\bthe previous result\b",
            "{{previous}}",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"\bprevious result\b",
            "{{previous}}",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"\bresult from step\s+(\d+)\b",
            lambda match: (
                "{{step."
                + match.group(1)
                + "}}"
            ),
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"\bstep\s+(\d+)\s+result\b",
            lambda match: (
                "{{step."
                + match.group(1)
                + "}}"
            ),
            text,
            flags=re.IGNORECASE
        )

        return text

    # ---------------------------------
    # BUILD WORKFLOW
    # ---------------------------------

    def _build_workflow(
        self,
        request
    ):

        workflow = Workflow(
            goal=request
        )

        parts = [
            part.strip()
            for part
            in request.split(
                " then "
            )
            if part.strip()
        ]

        for part in parts:

            part = (
                self._normalize_references(
                    part
                )
            )

            lower = part.lower()

            # -------------------------
            # SAVE WORKFLOW RESULT
            # -------------------------

            save_match = re.match(
                r"^save\s+"
                r"(\{\{"
                r"(?:previous|step\.\d+)"
                r"(?:\.[a-zA-Z0-9_\.]+)?"
                r"\}\})"
                r"\s+to\s+(.+)$",
                part,
                re.IGNORECASE
            )

            if save_match:

                content_reference = (
                    save_match.group(1)
                )

                filename = (
                    save_match.group(2)
                    .strip()
                    .strip('"')
                )

                workflow.add_step(
                    "skill",
                    "file",
                    {
                        "operation": "write_text",
                        "filename": filename,
                        "content": (
                            content_reference
                        )
                    }
                )

                continue

            # -------------------------
            # EXTERNAL AGENT
            #
            # Must come before TERMINAL,
            # because "run agent ..." also
            # starts with "run ".
            # -------------------------

            if (
                lower.startswith(
                    "run agent "
                )
                or lower.startswith(
                    "run external agent "
                )
            ):

                workflow.add_step(
                    "skill",
                    "providers",
                    {
                        "message": part
                    }
                )

                continue

            # -------------------------
            # EXTERNAL AGENT INFO/PREVIEW
            # -------------------------

            if (
                lower.startswith(
                    "preview agent "
                )
                or lower.startswith(
                    "preview external agent "
                )
                or lower.startswith(
                    "external agent info "
                )
                or lower.startswith(
                    "agent info "
                )
                or lower in (
                    "show external agents",
                    "list external agents",
                    "external agents"
                )
            ):

                workflow.add_step(
                    "skill",
                    "providers",
                    {
                        "message": part
                    }
                )

                continue

            # -------------------------
            # TERMINAL
            # -------------------------

            if (
                lower.startswith(
                    "run "
                )
                or lower.startswith(
                    "execute "
                )
                or lower.startswith(
                    "terminal "
                )
            ):

                workflow.add_step(
                    "skill",
                    "terminal",
                    {
                        "message": part
                    }
                )

                continue

            # -------------------------
            # OLLAMA
            # -------------------------

            if lower.startswith(
                "ask ollama "
            ):

                workflow.add_step(
                    "skill",
                    "providers",
                    {
                        "message": part
                    }
                )

                continue

            # -------------------------
            # OLLAMA MODELS
            # -------------------------

            if lower in (
                "show ollama models",
                "list ollama models",
                "ollama models"
            ):

                workflow.add_step(
                    "skill",
                    "providers",
                    {
                        "message": part
                    }
                )

                continue

            # -------------------------
            # PROVIDER STATUS
            # -------------------------

            if lower in (
                "show providers",
                "list providers",
                "show provider capabilities"
            ):

                workflow.add_step(
                    "skill",
                    "providers",
                    {
                        "message": part
                    }
                )

                continue

            # -------------------------
            # RESEARCH
            # -------------------------

            if lower.startswith(
                "research "
            ):

                workflow.add_step(
                    "skill",
                    "research",
                    {
                        "message": part
                    }
                )

                continue

            # -------------------------
            # WEB SEARCH
            # -------------------------

            if (
                lower.startswith(
                    "search "
                )
                or lower.startswith(
                    "look up "
                )
            ):

                search_message = (
                    part
                )

                if (
                    lower.startswith(
                        "search "
                    )
                    and not lower.startswith(
                        "search the web for "
                    )
                ):

                    query = part[
                        len("search "):
                    ].strip()

                    search_message = (
                        "search the web for "
                        + query
                    )

                workflow.add_step(
                    "skill",
                    "web_search",
                    {
                        "message": (
                            search_message
                        )
                    }
                )

                continue

            # -------------------------
            # OPEN APPLICATION
            # -------------------------

            if lower.startswith(
                "open "
            ):

                app = part[
                    len("open "):
                ].strip()

                workflow.add_step(
                    "provider",
                    "open_app",
                    {
                        "app": app
                    },
                    target="local_system"
                )

                continue

            # -------------------------
            # PROCESSES
            # -------------------------

            if lower in (
                "show running processes",
                "show processes",
                "list processes"
            ):

                workflow.add_step(
                    "provider",
                    "list_processes",
                    {},
                    target="local_system"
                )

                continue

        return workflow

    # ---------------------------------
    # FORMAT RESULT
    # ---------------------------------

    def _format_result(
        self,
        workflow,
        result
    ):

        output = (
            f"Aether: Workflow: "
            f"{workflow.goal}\n"
            f"ID: {workflow.workflow_id}\n\n"
        )

        for index, item in enumerate(
            workflow.results,
            start=1
        ):

            output += (
                f"Step {index}: "
            )

            if item.get(
                "success"
            ):

                output += (
                    "complete\n"
                )

                response = (
                    item.get(
                        "response"
                    )
                )

                if response:

                    output += (
                        f"{response}\n"
                    )

                elif (
                    item.get(
                        "capability"
                    )
                    == "open_app"
                ):

                    output += (
                        "Application opened.\n"
                    )

                elif (
                    item.get(
                        "capability"
                    )
                    == "list_processes"
                ):

                    count = (
                        item.get(
                            "count",
                            0
                        )
                    )

                    output += (
                        f"{count} running "
                        "processes detected.\n"
                    )

            else:

                output += (
                    "failed\n"
                )

                output += (
                    item.get(
                        "error",
                        "Unknown error."
                    )
                    + "\n"
                )

            output += "\n"

        # ---------------------------------
        # PAUSED
        # ---------------------------------

        if result.get(
            "paused"
        ):

            permission_message = (
                result.get(
                    "permission_message",
                    ""
                )
            )

            output += (
                "Workflow status: paused\n"
                f"Progress: "
                f"{result.get('progress')}%\n\n"
                f"{permission_message}"
            )

            return (
                output.rstrip()
            )

        output += (
            f"Workflow status: "
            f"{result.get('status')}\n"
            f"Progress: "
            f"{result.get('progress')}%"
        )

        return (
            output.rstrip()
        )

    # ---------------------------------
    # MISSION EXECUTION
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None