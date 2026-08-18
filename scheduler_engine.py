import threading
import time

from datetime import datetime, timedelta

from scheduler_store import SchedulerStore


class SchedulerEngine:
    """
    Persistent background scheduler for Aether.

    SchedulerEngine decides WHEN work becomes due.

    Actual work is still executed through
    Aether's existing WorkflowSkill.
    """

    CHECK_INTERVAL = 1.0

    def __init__(
        self,
        skill_manager
    ):

        self.skill_manager = (
            skill_manager
        )

        self.store = (
            SchedulerStore()
        )

        self._thread = None

        self._stop_event = (
            threading.Event()
        )

    # ---------------------------------
    # START
    # ---------------------------------

    def start(
        self
    ):

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):

            return False

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._worker,
            name="AetherScheduler",
            daemon=True
        )

        self._thread.start()

        return True

    # ---------------------------------
    # STOP
    # ---------------------------------

    def stop(
        self
    ):

        self._stop_event.set()

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):

            self._thread.join(
                timeout=2
            )

    # ---------------------------------
    # WORKER
    # ---------------------------------

    def _worker(
        self
    ):

        while not self._stop_event.is_set():

            try:

                self.run_due_jobs()

            except Exception as error:

                print(
                    "\nAether Scheduler error: "
                    f"{error}"
                )

            self._stop_event.wait(
                self.CHECK_INTERVAL
            )

    # ---------------------------------
    # RUN DUE JOBS
    # ---------------------------------

    def run_due_jobs(
        self
    ):

        now = datetime.now()

        jobs = self.store.load_all()

        for job in jobs:

            if not job.enabled:

                continue

            if not job.next_run:

                continue

            try:

                due_time = (
                    datetime.fromisoformat(
                        job.next_run
                    )
                )

            except ValueError:

                job.enabled = False

                job.mark_run(
                    "invalid_schedule"
                )

                self.store.save(
                    job
                )

                continue

            if due_time > now:

                continue

            self._run_job(
                job
            )

    # ---------------------------------
    # RUN ONE
    # ---------------------------------

    def _run_job(
        self,
        job
    ):

        # Advance or disable the schedule BEFORE
        # execution so a long-running task cannot
        # accidentally trigger twice.
        if job.recurrence == "daily":

            previous_due = (
                datetime.fromisoformat(
                    job.next_run
                )
            )

            next_run = (
                previous_due
                + timedelta(
                    days=1
                )
            )

            while next_run <= datetime.now():

                next_run += timedelta(
                    days=1
                )

            job.next_run = (
                next_run.isoformat(
                    timespec="seconds"
                )
            )

        else:

            job.enabled = False
            job.next_run = None

        job.touch()

        self.store.save(
            job
        )

        print(
            "\n"
            + "=" * 50
        )

        print(
            "Aether Scheduler: "
            f"Running {job.job_id}"
        )

        print(
            f"Goal: {job.goal}"
        )

        print(
            "=" * 50
        )

        workflow_message = (
            "workflow "
            + job.workflow_request
        )

        try:

            response = (
                self.skill_manager
                .handle(
                    workflow_message
                )
            )

        except Exception as error:

            job.mark_run(
                "failed",
                str(
                    error
                )
            )

            self.store.save(
                job
            )

            print(
                "Aether Scheduler: Job failed.\n"
                f"{error}"
            )

            return

        status = (
            self._response_status(
                response
            )
        )

        job.mark_run(
            status,
            response
        )

        self.store.save(
            job
        )

        print(
            response
            or "Aether Scheduler: "
               "Job returned no response."
        )

        print(
            "\nAether Scheduler: "
            f"{job.job_id} -> {status}"
        )

    # ---------------------------------
    # RESPONSE STATUS
    # ---------------------------------

    def _response_status(
        self,
        response
    ):

        text = str(
            response
            or ""
        ).lower()

        if (
            "workflow status: paused"
            in text
        ):

            return "paused"

        if (
            "workflow status: failed"
            in text
        ):

            return "failed"

        if (
            "workflow status: completed"
            in text
        ):

            return "completed"

        return "unknown"