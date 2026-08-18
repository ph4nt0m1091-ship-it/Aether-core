import json
import re

from datetime import datetime
from uuid import uuid4


class Workflow:
    """
    Represents a sequence of actions for Aether.

    Workflows are separate from predefined missions.
    They are intended for dynamic, user-requested work.

    Workflow results can be referenced by later steps:

    {{previous}}
    {{step.1}}
    {{step.2}}
    """

    REFERENCE_PATTERN = re.compile(
        r"\{\{\s*(previous|step\.(\d+))\s*\}\}",
        re.IGNORECASE
    )

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

        Used when a workflow pauses before
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
    # RESULT ACCESS
    # ---------------------------------

    def previous_result(
        self
    ):

        if not self.results:

            raise ValueError(
                "There is no previous workflow result."
            )

        return self.results[-1]

    def step_result(
        self,
        step_number
    ):

        try:

            step_number = int(
                step_number
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "Workflow step reference is invalid."
            )

        index = (
            step_number - 1
        )

        if (
            index < 0
            or index >= len(self.results)
        ):

            raise ValueError(
                f"Workflow step {step_number} "
                "does not have a result yet."
            )

        return self.results[
            index
        ]

    # ---------------------------------
    # RESULT → TEXT
    # ---------------------------------

    def result_text(
        self,
        result
    ):

        if result is None:

            return ""

        if isinstance(
            result,
            str
        ):

            return result

        if not isinstance(
            result,
            dict
        ):

            return str(
                result
            )

        # Prefer clean machine-readable output
        # over Aether's formatted display text.
        for key in (
            "output",
            "content",
            "answer",
            "stdout",
            "response"
        ):

            value = result.get(
                key
            )

            if value is not None:

                if isinstance(
                    value,
                    str
                ):

                    return value

                return json.dumps(
                    value,
                    ensure_ascii=False,
                    indent=2,
                    default=str
                )

        return json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=str
        )

    # ---------------------------------
    # REFERENCE RESOLUTION
    # ---------------------------------

    def resolve_references(
        self,
        value
    ):

        if isinstance(
            value,
            dict
        ):

            return {
                key: self.resolve_references(
                    item
                )
                for key, item
                in value.items()
            }

        if isinstance(
            value,
            list
        ):

            return [
                self.resolve_references(
                    item
                )
                for item in value
            ]

        if not isinstance(
            value,
            str
        ):

            return value

        def replace_reference(
            match
        ):

            reference = (
                match.group(1)
                .lower()
            )

            if reference == "previous":

                result = (
                    self.previous_result()
                )

                return self.result_text(
                    result
                )

            step_number = (
                match.group(2)
            )

            result = self.step_result(
                step_number
            )

            return self.result_text(
                result
            )

        return self.REFERENCE_PATTERN.sub(
            replace_reference,
            value
        )

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