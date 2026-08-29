class WorkflowObserver:
    """
    Builds deterministic, read-only workflow recovery telemetry.

    It does not execute actions, change permissions, route
    providers, alter fallback policy, or persist prompts.
    """

    def snapshot(self, workflow, final_result=None):
        results = list(getattr(workflow, "results", []) or [])

        recovered_steps = 0
        retry_recoveries = 0
        fallback_recoveries = 0
        adaptive_recoveries = 0
        retry_skips = 0
        failed_steps = 0
        latest_recovery = None

        for index, item in enumerate(results, start=1):
            if not isinstance(item, dict):
                continue

            if not item.get("success", False):
                failed_steps += 1

            recovery = item.get("recovery")

            if not isinstance(recovery, dict):
                continue

            recovered = bool(
                recovery.get("retry_succeeded")
                or recovery.get("fallback_succeeded")
            )

            if recovered:
                recovered_steps += 1

            if recovery.get("retry_succeeded"):
                retry_recoveries += 1

            if recovery.get("fallback_succeeded"):
                fallback_recoveries += 1

            if recovery.get("adaptive_recovery"):
                adaptive_recoveries += 1

            if recovery.get("retry_skipped"):
                retry_skips += 1

            latest_recovery = {
                "step": index,
                "recovered": recovered,
                "retry_succeeded": bool(
                    recovery.get("retry_succeeded")
                ),
                "fallback_succeeded": bool(
                    recovery.get("fallback_succeeded")
                ),
                "adaptive_recovery": bool(
                    recovery.get("adaptive_recovery")
                ),
                "retry_skipped": bool(
                    recovery.get("retry_skipped")
                ),
                "fallback_from_model": recovery.get(
                    "fallback_from_model"
                ),
                "fallback_model": recovery.get(
                    "fallback_model"
                ),
                "repeat_failure_count": int(
                    recovery.get("repeat_failure_count", 0) or 0
                ),
                "summary": str(
                    item.get("recovery_summary", "") or ""
                )
            }

        try:
            progress = workflow.progress()
        except Exception:
            progress = (
                final_result.get("progress")
                if isinstance(final_result, dict)
                else None
            )

        return {
            "workflow_id": str(
                getattr(workflow, "workflow_id", "") or ""
            ),
            "status": getattr(workflow, "status", "unknown"),
            "progress": progress,
            "result_count": len(results),
            "failed_steps": failed_steps,
            "recovered_steps": recovered_steps,
            "retry_recoveries": retry_recoveries,
            "fallback_recoveries": fallback_recoveries,
            "adaptive_recoveries": adaptive_recoveries,
            "retry_skips": retry_skips,
            "latest_recovery": latest_recovery,
            "recovery_used": bool(
                recovered_steps or adaptive_recoveries
            )
        }

    def summary(self, workflow, final_result=None):
        snapshot = self.snapshot(
            workflow,
            final_result=final_result
        )

        if not snapshot["recovery_used"]:
            return "No automatic recovery was needed."

        pieces = []

        if snapshot["adaptive_recoveries"]:
            pieces.append(
                f"{snapshot['adaptive_recoveries']} adaptive recovery"
            )

        if snapshot["retry_recoveries"]:
            pieces.append(
                f"{snapshot['retry_recoveries']} retry recovery"
            )

        if snapshot["fallback_recoveries"]:
            pieces.append(
                f"{snapshot['fallback_recoveries']} local fallback recovery"
            )

        if snapshot["retry_skips"]:
            pieces.append(
                f"{snapshot['retry_skips']} redundant retry skipped"
            )

        return "Recovery activity: " + ", ".join(pieces) + "."
