from datetime import datetime
from uuid import uuid4


class ScheduledJob:
    """
    Persistent scheduled work for Aether.
    """

    def __init__(
        self,
        goal="",
        workflow_request="",
        next_run=None,
        recurrence="once",
        job_id=None,
        enabled=True,
        created_at=None,
        updated_at=None,
        last_run=None,
        last_status=None,
        last_response=None
    ):

        self.job_id = (
            job_id
            or f"job_{uuid4().hex[:12]}"
        )

        self.goal = goal

        self.workflow_request = (
            workflow_request
        )

        self.next_run = next_run

        self.recurrence = (
            recurrence
        )

        self.enabled = bool(
            enabled
        )

        now = self._timestamp()

        self.created_at = (
            created_at
            or now
        )

        self.updated_at = (
            updated_at
            or now
        )

        self.last_run = (
            last_run
        )

        self.last_status = (
            last_status
        )

        self.last_response = (
            last_response
        )

    # ---------------------------------
    # STATE
    # ---------------------------------

    def touch(
        self
    ):

        self.updated_at = (
            self._timestamp()
        )

    def mark_run(
        self,
        status,
        response=None
    ):

        self.last_run = (
            self._timestamp()
        )

        self.last_status = (
            status
        )

        self.last_response = (
            response
        )

        self.touch()

    # ---------------------------------
    # PERSISTENCE
    # ---------------------------------

    def to_dict(
        self
    ):

        return {
            "job_id": self.job_id,
            "goal": self.goal,
            "workflow_request": (
                self.workflow_request
            ),
            "next_run": (
                self.next_run
            ),
            "recurrence": (
                self.recurrence
            ),
            "enabled": (
                self.enabled
            ),
            "created_at": (
                self.created_at
            ),
            "updated_at": (
                self.updated_at
            ),
            "last_run": (
                self.last_run
            ),
            "last_status": (
                self.last_status
            ),
            "last_response": (
                self.last_response
            )
        }

    @classmethod
    def from_dict(
        cls,
        data
    ):

        return cls(
            job_id=data.get(
                "job_id"
            ),
            goal=data.get(
                "goal",
                ""
            ),
            workflow_request=data.get(
                "workflow_request",
                ""
            ),
            next_run=data.get(
                "next_run"
            ),
            recurrence=data.get(
                "recurrence",
                "once"
            ),
            enabled=data.get(
                "enabled",
                True
            ),
            created_at=data.get(
                "created_at"
            ),
            updated_at=data.get(
                "updated_at"
            ),
            last_run=data.get(
                "last_run"
            ),
            last_status=data.get(
                "last_status"
            ),
            last_response=data.get(
                "last_response"
            )
        )

    # ---------------------------------
    # TIMESTAMP
    # ---------------------------------

    def _timestamp(
        self
    ):

        return (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )