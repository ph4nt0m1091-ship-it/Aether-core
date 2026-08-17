from workflow import Workflow
from workflow_engine import WorkflowEngine


class WorkflowSkill:
    """
    Runs multi-step Aether workflows.

    Example:

    workflow research motor drivers then open vscode
    """

    name = "workflow"

    description = (
        "Coordinates multiple Aether skills and "
        "providers as one workflow."
    )

    def __init__(
        self,
        memory,
        skill_manager=None
    ):

        self.memory = memory

        self.skill_manager = (
            skill_manager
        )

        self.engine = None

    # ---------------------------------
    # CONNECT MANAGER
    # ---------------------------------

    def connect(
        self,
        skill_manager
    ):

        self.skill_manager = (
            skill_manager
        )

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

        lower = (
            message
            .strip()
            .lower()
        )

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
            for part
            in request.split(
                " then "
            )
            if part.strip()
        ]

        for part in parts:

            lower = part.lower()

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

                if lower.startswith(
                    "search "
                ) and not lower.startswith(
                    "search the web for "
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
            # PROCESS LIST
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
            f"{workflow.goal}\n\n"
        )

        for index, item in enumerate(
            result.get(
                "results",
                []
            ),
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