from datetime import datetime
from uuid import uuid4


class Workflow:
    """
    Represents a sequence of actions for Aether.

    Workflows are separate from predefined missions.
    They are intended for dynamic, user-requested work.
    """

    def __init__(
        self,
        goal="",
        workflow_id=None,
        steps=None,
        current_step=0,
        results=None,
        status="pending",
        created_at=None,
        updated_at=None
    ):

        self.workflow_id = (
            workflow_id
            or f"wf_{uuid4().hex[:12]}"
        )

        self.goal = goal

        self.steps = (
            steps
            if isinstance(steps, list)
            else []
        )

        self.current_step = current_step

        self.results = (
            results
            if isinstance(results, list)
            else []
        )

        self.status = status

        now = self._timestamp()

        self.created_at = (
            created_at
            or now
        )

        self.updated_at = (
            updated_at
            or now
        )

    # ---------------------------------
    # ADD STEP
    # ---------------------------------

    def add_step(
        self,
        step_type,
        action,
        data=None,
        target=None
    ):

        self.steps.append(
            {
                "type": step_type,
                "action": action,
                "data": data or {},
                "target": target
            }
        )

        self.touch()

    # ---------------------------------
    # STATE
    # ---------------------------------

    def has_next_step(self):

        return (
            self.current_step
            < len(self.steps)
        )

    def peek_next_step(self):

        if not self.has_next_step():

            return None

        return self.steps[
            self.current_step
        ]

    def next_step(self):

        if not self.has_next_step():

            return None

        step = self.steps[
            self.current_step
        ]

        self.current_step += 1

        self.touch()

        return step

    def rewind_one_step(self):
        """
        Move back one step.

        This is used when a workflow pauses before
        an action actually executes.
        """

        if self.current_step > 0:

            self.current_step -= 1

            self.touch()

    def add_result(
        self,
        result
    ):

        self.results.append(
            result
        )

        self.touch()

    def progress(self):

        total = len(
            self.steps
        )

        if total == 0:

            return 100

        return int(
            (
                self.current_step
                / total
            )
            * 100
        )

    def reset(self):

        self.current_step = 0
        self.results = []
        self.status = "pending"

        self.touch()

    # ---------------------------------
    # PERSISTENCE
    # ---------------------------------

    def to_dict(self):

        return {
            "workflow_id": self.workflow_id,
            "goal": self.goal,
            "steps": self.steps,
            "current_step": self.current_step,
            "results": self.results,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(
        cls,
        data
    ):

        return cls(
            workflow_id=data.get(
                "workflow_id"
            ),
            goal=data.get(
                "goal",
                ""
            ),
            steps=data.get(
                "steps",
                []
            ),
            current_step=data.get(
                "current_step",
                0
            ),
            results=data.get(
                "results",
                []
            ),
            status=data.get(
                "status",
                "pending"
            ),
            created_at=data.get(
                "created_at"
            ),
            updated_at=data.get(
                "updated_at"
            )
        )

    # ---------------------------------
    # TIMESTAMPS
    # ---------------------------------

    def touch(self):

        self.updated_at = (
            self._timestamp()
        )

    def _timestamp(self):

        return datetime.now().isoformat(
            timespec="seconds"
        )

    def __len__(self):

        return len(
            self.steps
        )