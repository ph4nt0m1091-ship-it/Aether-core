import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class ExecutionLedger:
    """
    Persistent action history for Aether.

    Records workflow actions, providers, outcomes,
    timestamps, and execution status.
    """

    def __init__(
        self,
        path="storage/execution_history.json"
    ):

        self.path = Path(
            path
        )

    # ---------------------------------
    # RECORD
    # ---------------------------------

    def record(
        self,
        workflow_id,
        step,
        result=None,
        status="started"
    ):

        entry = {
            "execution_id": (
                f"exec_{uuid4().hex[:12]}"
            ),
            "workflow_id": workflow_id,
            "timestamp": self._timestamp(),
            "status": status,
            "step_type": step.get(
                "type"
            ),
            "action": step.get(
                "action"
            ),
            "target": step.get(
                "target"
            ),
            "data": self._safe_data(
                step.get(
                    "data",
                    {}
                )
            ),
            "success": None,
            "paused": False,
            "provider": None,
            "error": None
        }

        if isinstance(
            result,
            dict
        ):

            entry["success"] = result.get(
                "success"
            )

            entry["paused"] = result.get(
                "paused",
                False
            )

            entry["provider"] = result.get(
                "provider"
            )

            entry["error"] = result.get(
                "error"
            )

        entries = self.load_all()

        entries.append(
            entry
        )

        self.save_all(
            entries
        )

        return entry

    # ---------------------------------
    # LOAD
    # ---------------------------------

    def load_all(self):

        if not self.path.exists():

            return []

        try:

            with self.path.open(
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

        except (
            OSError,
            json.JSONDecodeError
        ):

            return []

        if not isinstance(
            data,
            list
        ):

            return []

        return data

    # ---------------------------------
    # SAVE
    # ---------------------------------

    def save_all(
        self,
        entries
    ):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with self.path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                entries,
                file,
                indent=4
            )

    # ---------------------------------
    # WORKFLOW HISTORY
    # ---------------------------------

    def for_workflow(
        self,
        workflow_id
    ):

        return [
            entry
            for entry in self.load_all()
            if (
                entry.get(
                    "workflow_id"
                )
                == workflow_id
            )
        ]

    # ---------------------------------
    # RECENT HISTORY
    # ---------------------------------

    def recent(
        self,
        limit=20
    ):

        entries = self.load_all()

        return entries[
            -limit:
        ]

    # ---------------------------------
    # SAFE DATA
    # ---------------------------------

    def _safe_data(
        self,
        data
    ):
        """
        Remove fields that should not be persisted
        if sensitive values are introduced later.
        """

        if not isinstance(
            data,
            dict
        ):

            return {}

        blocked_keys = {
            "password",
            "token",
            "api_key",
            "secret",
            "authorization"
        }

        cleaned = {}

        for key, value in data.items():

            if key.lower() in blocked_keys:

                cleaned[key] = (
                    "[REDACTED]"
                )

            else:

                cleaned[key] = value

        return cleaned

    # ---------------------------------
    # TIMESTAMP
    # ---------------------------------

    def _timestamp(self):

        return datetime.now().isoformat(
            timespec="seconds"
        )