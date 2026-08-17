from workflow import Workflow
from workflow_engine import WorkflowEngine


class WorkflowSkill:
    """
    Coordinates multi-step Aether workflows.

    Workflows can pause for terminal permission
    and resume after the user approves or denies.
    """

    name = "workflow"

    description = (
        "Coordinates multiple Aether skills and "
        "providers as resumable workflows."
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

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        message = message.strip()

        # ---------------------------------
        # RESUME PAUSED WORKFLOW
        # ---------------------------------

        if self.pending_workflow is not None:

            return self._handle_pending_workflow(
                message
            )

        lower = message.lower()

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

            self.pending_workflow = workflow

        return self._format_result(
            workflow,
            result
        )

    # ---------------------------------
    # HANDLE PAUSED WORKFLOW
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

            self.pending_workflow = None

            return (
                "Aether: Terminal skill is unavailable. "
                "Workflow cancelled."
            )

        permission_response = (
            terminal_skill.handle(
                message
            )
        )

        # User hasn't answered yes/no yet.
        if terminal_skill.permissions.has_pending():

            return permission_response

        workflow = self.pending_workflow

        # ---------------------------------
        # CANCELLED
        # ---------------------------------

        if (
            permission_response
            == "Aether: Command cancelled."
        ):

            workflow.status = "cancelled"

            self.pending_workflow = None

            return (
                f"{permission_response}\n\n"
                "Aether: Workflow cancelled.\n"
                f"Progress: {workflow.progress()}%"
            )

        # ---------------------------------
        # COMMAND FAILURE
        # ---------------------------------

        if permission_response.startswith(
            "Aether: Command failed."
        ):

            workflow.add_result(
                {
                    "success": False,
                    "type": "skill",
                    "action": "terminal",
                    "response": permission_response,
                    "error": permission_response
                }
            )

            workflow.status = "failed"

            self.pending_workflow = None

            return self._format_result(
                workflow,
                {
                    "success": False,
                    "paused": False,
                    "status": "failed",
                    "progress": workflow.progress(),
                    "results": workflow.results
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
                "response": permission_response
            }
        )

        self.pending_workflow = None

        # Continue with remaining steps.
        result = self.engine.execute(
            workflow
        )

        if result.get(
            "paused"
        ):

            self.pending_workflow = workflow

        return self._format_result(
            workflow,
            result
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
            for part in request.split(
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

                message = part

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

                    message = (
                        "search the web for "
                        + query
                    )

                workflow.add_step(
                    "skill",
                    "web_search",
                    {
                        "message": message
                    }
                )

                continue

            # -------------------------
            # OPEN APP
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
    # FORMAT
    # ---------------------------------

    def _format_result(
        self,
        workflow,
        result
    ):

        output = (
            f"Aether: Workflow: "
            f"{workflow.goal}\n\n"
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

                output += "complete\n"

                response = item.get(
                    "response"
                )

                if response:

                    output += (
                        f"{response}\n"
                    )

                elif item.get(
                    "capability"
                ) == "open_app":

                    output += (
                        "Application opened.\n"
                    )

                elif item.get(
                    "capability"
                ) == "list_processes":

                    count = item.get(
                        "count",
                        0
                    )

                    output += (
                        f"{count} running "
                        "processes detected.\n"
                    )

            else:

                output += "failed\n"

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

    def execute(
        self,
        step
    ):

        return None