from execution_ledger import ExecutionLedger
from failure_memory import FailureMemory


class HistorySkill:
    """
    Lets Aether inspect persistent execution history,
    recovery history, and recurring operational failures.
    """

    name = "history"

    description = (
        "Shows Aether's recent action, workflow, recovery, "
        "and operational failure history."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory
        self.ledger = ExecutionLedger()
        self.failure_memory = FailureMemory()

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

        recovery_commands = {
            "show recovery history",
            "recovery history",
            "show recent recoveries",
            "recent recoveries"
        }

        failure_commands = {
            "show failure patterns",
            "failure patterns",
            "show recurring failures",
            "recurring failures",
            "show failure memory",
            "failure memory"
        }

        if lower in recent_commands:

            return self._recent_history()

        if lower in workflow_commands:

            return self._workflow_history()

        if lower in recovery_commands:

            return self._recovery_history()

        if lower in failure_commands:

            return self._failure_patterns()

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
                    "status": "unknown",
                    "recoveries": 0,
                    "failures": 0
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

            if status in (
                "fallback_completed",
                "completed_after_retry"
            ):

                workflow[
                    "recoveries"
                ] += 1

            if status in (
                "failed",
                "fallback_failed"
            ):

                workflow[
                    "failures"
                ] += 1

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
                f"  Failures observed: "
                f"{workflow['failures']}\n"
                f"  Recovery events: "
                f"{workflow['recoveries']}\n"
                f"  Last activity: "
                f"{workflow['last_timestamp']}\n\n"
            )

        return output.rstrip()

    # ---------------------------------
    # RECOVERY HISTORY
    # ---------------------------------

    def _recovery_history(
        self,
        limit=10
    ):

        entries = (
            self.failure_memory
            .recent_recoveries(
                limit=limit
            )
        )

        if not entries:

            return (
                "Aether: No automatic recoveries "
                "have been recorded yet."
            )

        output = (
            "Aether: Recovery History\n\n"
        )

        for entry in reversed(
            entries
        ):

            output += (
                f"- {entry.get('action', 'unknown')}\n"
                f"  Workflow: "
                f"{entry.get('workflow_id', 'unknown')}\n"
                f"  Time: "
                f"{entry.get('timestamp', 'unknown')}\n"
            )

            if entry.get(
                "retry_succeeded"
            ):

                output += (
                    "  Recovery: retry succeeded\n"
                )

            elif entry.get(
                "fallback_succeeded"
            ):

                from_model = entry.get(
                    "fallback_from_model",
                    ""
                )

                to_model = entry.get(
                    "fallback_model",
                    ""
                )

                output += (
                    "  Recovery: local fallback succeeded\n"
                )

                if (
                    from_model
                    or to_model
                ):

                    output += (
                        f"  Model fallback: "
                        f"{from_model or 'unknown'} "
                        f"-> {to_model or 'unknown'}\n"
                    )

            else:

                output += (
                    "  Recovery: recorded without "
                    "successful automatic recovery\n"
                )

            output += "\n"

        return output.rstrip()

    # ---------------------------------
    # FAILURE PATTERNS
    # ---------------------------------

    def _failure_patterns(
        self,
        minimum_count=2,
        limit=10
    ):

        patterns = (
            self.failure_memory
            .repeated_patterns(
                minimum_count=minimum_count,
                limit=limit
            )
        )

        if not patterns:

            return (
                "Aether: No recurring operational "
                "failure patterns have been detected."
            )

        output = (
            "Aether: Recurring Failure Patterns\n\n"
        )

        for pattern in patterns:

            output += (
                f"- {pattern.get('action', 'unknown')}\n"
                f"  Count: {pattern.get('count', 0)}\n"
                f"  Failure type: "
                f"{pattern.get('failure_type', 'unknown')}\n"
            )

            provider = pattern.get(
                "provider"
            )

            target = pattern.get(
                "target"
            )

            model = pattern.get(
                "model"
            )

            if provider:

                output += (
                    f"  Provider: {provider}\n"
                )

            elif target:

                output += (
                    f"  Target: {target}\n"
                )

            if model:

                output += (
                    f"  Model: {model}\n"
                )

            error = pattern.get(
                "error"
            )

            if error:

                output += (
                    f"  Error: {error}\n"
                )

            output += (
                f"  Last seen: "
                f"{pattern.get('last_seen', 'unknown')}\n\n"
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
