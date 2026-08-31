import json
import os

from datetime import datetime
from pathlib import Path


class BackgroundJobHistory:
    VERSION = 1
    MAX_EVENTS = 200

    def __init__(
        self,
        path="storage/background_job_history.json"
    ):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return {
                "version": self.VERSION,
                "events": []
            }

        try:
            data = json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except (
            OSError,
            json.JSONDecodeError
        ):
            return {
                "version": self.VERSION,
                "events": []
            }

        if not isinstance(data, dict):
            return {
                "version": self.VERSION,
                "events": []
            }

        events = data.get("events", [])
        if not isinstance(events, list):
            events = []

        return {
            "version": self.VERSION,
            "events": events[-self.MAX_EVENTS:]
        }

    def record(
        self,
        job_id,
        status,
        workflow_id=None,
        observability=None,
        recovery_activity=None,
        error=None
    ):
        data = self.load()

        event = {
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
            "job_id": str(job_id or ""),
            "workflow_id": (
                str(workflow_id)
                if workflow_id
                else None
            ),
            "status": str(status or "unknown"),
            "observability": self._safe_observability(
                observability
            ),
            "recovery_activity": (
                self._clean_text(
                    recovery_activity,
                    limit=500
                )
                if recovery_activity
                else None
            ),
            "error": (
                self._clean_text(
                    error,
                    limit=500
                )
                if error
                else None
            )
        }

        data["events"].append(event)
        data["events"] = data["events"][-self.MAX_EVENTS:]
        self._save(data)
        return event

    def recent(self, limit=20):
        try:
            limit = max(1, int(limit))
        except (
            TypeError,
            ValueError
        ):
            limit = 20

        return self.load().get(
            "events",
            []
        )[-limit:][::-1]

    def _safe_observability(self, observability):
        if not isinstance(observability, dict):
            return None

        latest = observability.get("latest_recovery")
        safe_latest = None

        if isinstance(latest, dict):
            safe_latest = {
                "step": latest.get("step"),
                "recovered": bool(
                    latest.get("recovered")
                ),
                "retry_succeeded": bool(
                    latest.get("retry_succeeded")
                ),
                "fallback_succeeded": bool(
                    latest.get("fallback_succeeded")
                ),
                "adaptive_recovery": bool(
                    latest.get("adaptive_recovery")
                ),
                "retry_skipped": bool(
                    latest.get("retry_skipped")
                ),
                "fallback_from_model": (
                    self._clean_text(
                        latest.get(
                            "fallback_from_model"
                        ),
                        limit=100
                    )
                    if latest.get(
                        "fallback_from_model"
                    )
                    else None
                ),
                "fallback_model": (
                    self._clean_text(
                        latest.get("fallback_model"),
                        limit=100
                    )
                    if latest.get("fallback_model")
                    else None
                ),
                "repeat_failure_count": int(
                    latest.get(
                        "repeat_failure_count",
                        0
                    )
                    or 0
                )
            }

        return {
            "status": self._clean_text(
                observability.get("status", "unknown"),
                limit=50
            ),
            "progress": observability.get("progress"),
            "result_count": int(
                observability.get("result_count", 0)
                or 0
            ),
            "failed_steps": int(
                observability.get("failed_steps", 0)
                or 0
            ),
            "recovered_steps": int(
                observability.get("recovered_steps", 0)
                or 0
            ),
            "retry_recoveries": int(
                observability.get(
                    "retry_recoveries",
                    0
                )
                or 0
            ),
            "fallback_recoveries": int(
                observability.get(
                    "fallback_recoveries",
                    0
                )
                or 0
            ),
            "adaptive_recoveries": int(
                observability.get(
                    "adaptive_recoveries",
                    0
                )
                or 0
            ),
            "retry_skips": int(
                observability.get("retry_skips", 0)
                or 0
            ),
            "recovery_used": bool(
                observability.get("recovery_used")
            ),
            "latest_recovery": safe_latest
        }

    def _clean_text(self, value, limit):
        text = str(value or "")
        lowered = text.lower()

        sensitive_markers = (
            "api key",
            "apikey",
            "authorization:",
            "bearer ",
            "password=",
            "token="
        )

        for marker in sensitive_markers:
            index = lowered.find(marker)
            if index != -1:
                text = text[:index] + "[REDACTED]"
                break

        return text[:limit]

    def _save(self, data):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temp_path = self.path.with_suffix(
            self.path.suffix
            + f".{os.getpid()}.tmp"
        )

        try:
            temp_path.write_text(
                json.dumps(
                    data,
                    indent=4
                ),
                encoding="utf-8"
            )
            temp_path.replace(self.path)
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
