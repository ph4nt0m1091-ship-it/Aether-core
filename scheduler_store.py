import json
from pathlib import Path

from scheduled_job import ScheduledJob


class SchedulerStore:
    """
    Persistent storage for Aether scheduled jobs.
    """

    def __init__(
        self,
        path="storage/scheduled_jobs.json"
    ):

        self.path = Path(
            path
        )

    # ---------------------------------
    # LOAD
    # ---------------------------------

    def load_all(
        self
    ):

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

        jobs = []

        for item in data:

            if not isinstance(
                item,
                dict
            ):

                continue

            jobs.append(
                ScheduledJob.from_dict(
                    item
                )
            )

        return jobs

    # ---------------------------------
    # SAVE ALL
    # ---------------------------------

    def save_all(
        self,
        jobs
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
                [
                    job.to_dict()
                    for job in jobs
                ],
                file,
                indent=4
            )

    # ---------------------------------
    # SAVE ONE
    # ---------------------------------

    def save(
        self,
        job
    ):

        jobs = self.load_all()

        replaced = False

        for index, existing in enumerate(
            jobs
        ):

            if (
                existing.job_id
                == job.job_id
            ):

                jobs[index] = (
                    job
                )

                replaced = True

                break

        if not replaced:

            jobs.append(
                job
            )

        self.save_all(
            jobs
        )

    # ---------------------------------
    # GET
    # ---------------------------------

    def get(
        self,
        job_id
    ):

        for job in self.load_all():

            if job.job_id == job_id:

                return job

        return None

    # ---------------------------------
    # DELETE
    # ---------------------------------

    def delete(
        self,
        job_id
    ):

        jobs = self.load_all()

        remaining = [
            job
            for job in jobs
            if job.job_id != job_id
        ]

        if len(remaining) == len(
            jobs
        ):

            return False

        self.save_all(
            remaining
        )

        return True