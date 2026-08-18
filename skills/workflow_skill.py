from workflow import Workflow
from workflow_engine import WorkflowEngine


class WorkflowSkill:
    """
    Coordinates persistent, resumable Aether workflows.

    Workflows can:
    - Execute multiple skills/providers
    - Use external AI providers through Aether skills
    - Pause for terminal permission
    - Resume after approval
    - Survive Aether restarts
    - Recover unfinished work safely

    Permission itself is never persisted.
    """

    name = "workflow"

    description = (
        "Coordinates persistent multi-step Aether workflows "
        "that can use external providers, pause, resume, "
        "and recover after restarts."
    )

    def __init__(
        self,
        memory,
        skill_manager=None
    ):

        self.memory = memory
        self.skill_manager = skill_manager

        self.engine = None

        # Workflow currently waiting for
        # an in-memory permission response.
        self.pending_workflow = None

        # Workflow discovered from persistent
        # storage after Aether starts.
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

        # A workflow that was "running" when
        # Aether stopped should be considered
        # recoverable rather than automatically
        # continuing without the user.
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

            return self._handle_pending_workflow(
                message
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
        # RESUME SAVED WORKFLOW
        # ---------------------------------

        if lower in (
            "resume workflow",
            "resume last workflow",
            "continue workflow",
            "continue last workflow"
        ):

            return self._resume_saved_workflow()

        # ---------------------------------
        # CANCEL SAVED WORKFLOW
        # ---------------------------------

        if lower in (
            "cancel workflow",
            "cancel current workflow"
        ):

            return self._cancel_saved_workflow()

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

        workflow = self._build_workflow(
            request
        )

        if len(workflow) == 0:

            return (
                "Aether: I couldn't build "
                "a workflow from that request."
            )

        result = self.engine.execute(
            workflow
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

        return self._format_result(
            workflow,
            result
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

        workflow = self.recovered_workflow

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

        # Engine execution will recreate any
        # required terminal permission request.
        #
        # A previously granted permission is
        # intentionally NOT restored.
        result = self.engine.execute(
            workflow
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

        return self._format_result(
            workflow,
            result
        )

    # ---------------------------------
    # HANDLE PAUSED PERMISSION
    # ---------------------------------

    def _handle_pending_workflow(
        self,
        message
    ):

        terminal_skill = (
            self.skill_manager
            .registry
            .get_skill(
                "terminal"
            )
        )

        if terminal_skill is None:

            workflow = (
                self.pending_workflow
            )

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
                "Aether: Terminal skill is unavailable. "
                "Workflow cancelled."
            )

        permission_response = (
            terminal_skill.handle(
                message
            )
        )

        # User did not provide a valid yes/no yet.
        if (
            terminal_skill
            .permissions
            .has_pending()
        ):

            return permission_response

        workflow = self.pending_workflow

        # ---------------------------------
        # USER DENIED
        # ---------------------------------

        if (
            permission_response
            == "Aether: Command cancelled."
        ):

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
        # THE PAUSED STEP WAS ATTEMPTED
        # ---------------------------------
        #
        # WorkflowEngine rewinds a step when
        # permission is required.
        #
        # TerminalSkill has now executed that
        # command after approval, so advance the
        # workflow past that step before continuing.

        if workflow.has_next_step():

            workflow.current_step += 1

            workflow.touch()

        # ---------------------------------
        # COMMAND FAILED
        # ---------------------------------

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

            return self._format_result(
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

        # ---------------------------------
        # APPROVED COMMAND COMPLETED
        # ---------------------------------

        workflow.add_result(
            {
                "success": True,
                "paused": False,
                "type": "skill",
                "action": "terminal",
                "response": (
                    permission_response
                )
            }
        )

        self.engine.store.save(
            workflow
        )

        self.pending_workflow = None

        # Continue remaining steps.
        result = self.engine.execute(
            workflow
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

        return self._format_result(
            workflow,
            result
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

        if terminal_skill is not None:

            terminal_skill.permissions.cancel()

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

            lower = part.lower()

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
            # OLLAMA PROVIDER
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
            # SHOW OLLAMA MODELS
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

                search_message = part

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

                response = item.get(
                    "response"
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

                    count = item.get(
                        "count",
                        0
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

            return output.rstrip()

        output += (
            f"Workflow status: "
            f"{result.get('status')}\n"
            f"Progress: "
            f"{result.get('progress')}%"
        )

        return output.rstrip()

    # ---------------------------------
    # MISSION EXECUTION
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None