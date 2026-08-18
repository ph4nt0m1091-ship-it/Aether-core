from execution_ledger import ExecutionLedger


class HistorySkill:
    """
    Lets Aether inspect its persistent execution history.
    """

    name = "history"

    description = (
        "Shows Aether's recent action and workflow "
        "execution history."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory
        self.ledger = ExecutionLedger()

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        message = message.strip()
        lower = message.lower()

        recent_commands = {
            "show action history",
            "show recent actions",
            "show execution history",
            "action history",
            "recent actions"
        }

        workflow_commands = {
            "show workflow history",
            "workflow history"
        }

        if lower in recent_commands:

            return self._recent_history()

        if lower in workflow_commands:

            return self._workflow_history()

        return None

    # ---------------------------------
    # RECENT HISTORY
    # ---------------------------------

    def _recent_history(
        self,
        limit=10
    ):

        entries = self.ledger.recent(
            limit=limit
        )

        if not entries:

            return (
                "Aether: No execution history "
                "has been recorded yet."
            )

        output = (
            "Aether: Recent Action History\n\n"
        )

        for entry in reversed(
            entries
        ):

            status = entry.get(
                "status",
                "unknown"
            )

            action = entry.get(
                "action",
                "unknown"
            )

            target = entry.get(
                "target"
            )

            provider = entry.get(
                "provider"
            )

            workflow_id = entry.get(
                "workflow_id",
                "unknown"
            )

            timestamp = entry.get(
                "timestamp",
                "unknown"
            )

            output += (
                f"- {status}: {action}\n"
                f"  Workflow: {workflow_id}\n"
                f"  Time: {timestamp}\n"
            )

            if provider:

                output += (
                    f"  Provider: {provider}\n"
                )

            elif target:

                output += (
                    f"  Target: {target}\n"
                )

            error = entry.get(
                "error"
            )

            if error:

                output += (
                    f"  Error: {error}\n"
                )

            output += "\n"

        return output.rstrip()

    # ---------------------------------
    # WORKFLOW HISTORY
    # ---------------------------------

    def _workflow_history(
        self,
        limit=50
    ):

        entries = self.ledger.recent(
            limit=limit
        )

        if not entries:

            return (
                "Aether: No workflow history "
                "has been recorded yet."
            )

        workflows = {}

        for entry in entries:

            workflow_id = entry.get(
                "workflow_id"
            )

            if not workflow_id:

                continue

            if workflow_id not in workflows:

                workflows[workflow_id] = {
                    "workflow_id": workflow_id,
                    "last_timestamp": entry.get(
                        "timestamp",
                        ""
                    ),
                    "actions": [],
                    "status": "unknown"
                }

            workflow = workflows[
                workflow_id
            ]

            workflow["last_timestamp"] = (
                entry.get(
                    "timestamp",
                    workflow["last_timestamp"]
                )
            )

            action = entry.get(
                "action"
            )

            if (
                action
                and action not in workflow["actions"]
            ):

                workflow["actions"].append(
                    action
                )

            status = entry.get(
                "status"
            )

            if status:

                workflow["status"] = status

        if not workflows:

            return (
                "Aether: No workflow history "
                "has been recorded yet."
            )

        ordered = list(
            workflows.values()
        )

        ordered.sort(
            key=lambda item: item[
                "last_timestamp"
            ],
            reverse=True
        )

        output = (
            "Aether: Workflow History\n\n"
        )

        for workflow in ordered[:10]:

            actions = ", ".join(
                workflow["actions"]
            )

            if not actions:

                actions = "No actions recorded"

            output += (
                f"- {workflow['workflow_id']}\n"
                f"  Status: {workflow['status']}\n"
                f"  Actions: {actions}\n"
                f"  Last activity: "
                f"{workflow['last_timestamp']}\n\n"
            )

        return output.rstrip()

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None