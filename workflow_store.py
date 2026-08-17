import json
from pathlib import Path

from workflow import Workflow


class WorkflowStore:
    """
    Persistent storage for Aether workflows.
    """

    def __init__(
        self,
        path="storage/workflows.json"
    ):

        self.path = Path(
            path
        )

    # ---------------------------------
    # LOAD ALL
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

        workflows = []

        for item in data:

            if not isinstance(
                item,
                dict
            ):

                continue

            workflows.append(
                Workflow.from_dict(
                    item
                )
            )

        return workflows

    # ---------------------------------
    # SAVE ALL
    # ---------------------------------

    def save_all(
        self,
        workflows
    ):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        data = [
            workflow.to_dict()
            for workflow in workflows
        ]

        with self.path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    # ---------------------------------
    # SAVE ONE
    # ---------------------------------

    def save(
        self,
        workflow
    ):

        workflows = self.load_all()

        replaced = False

        for index, existing in enumerate(
            workflows
        ):

            if (
                existing.workflow_id
                == workflow.workflow_id
            ):

                workflows[index] = (
                    workflow
                )

                replaced = True

                break

        if not replaced:

            workflows.append(
                workflow
            )

        self.save_all(
            workflows
        )

    # ---------------------------------
    # GET ONE
    # ---------------------------------

    def get(
        self,
        workflow_id
    ):

        for workflow in self.load_all():

            if (
                workflow.workflow_id
                == workflow_id
            ):

                return workflow

        return None

    # ---------------------------------
    # UNFINISHED
    # ---------------------------------

    def unfinished(self):

        return [
            workflow
            for workflow in self.load_all()
            if workflow.status in (
                "pending",
                "running",
                "paused"
            )
        ]

    # ---------------------------------
    # LATEST UNFINISHED
    # ---------------------------------

    def latest_unfinished(self):

        workflows = (
            self.unfinished()
        )

        if not workflows:

            return None

        workflows.sort(
            key=lambda item: (
                item.updated_at
                or ""
            ),
            reverse=True
        )

        return workflows[0]