import re
import threading

from datetime import datetime, timedelta

from background_job_history import BackgroundJobHistory
from runtime_lock import RuntimeLock
from scheduler_store import SchedulerStore
from workflow_observer import WorkflowObserver
from workflow_store import WorkflowStore


class SchedulerEngine:
    CHECK_INTERVAL = 1.0

    def __init__(self, skill_manager):
        self.skill_manager = skill_manager
        self.store = SchedulerStore()
        self.runtime_lock = RuntimeLock()
        self.workflow_store = WorkflowStore()
        self.workflow_observer = WorkflowObserver()
        self.job_history = BackgroundJobHistory()
        self._thread = None
        self._stop_event = threading.Event()
        self.is_owner = False

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return True
        if not self.runtime_lock.acquire():
            self.is_owner = False
            return False
        self.is_owner = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._worker,
            name="AetherScheduler",
            daemon=True
        )
        self._thread.start()
        return True

    def stop(self):
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self.is_owner:
            self.runtime_lock.release()
        self.is_owner = False

    def _worker(self):
        try:
            while not self._stop_event.is_set():
                try:
                    self.run_due_jobs()
                except Exception as error:
                    print(
                        "\nAether Scheduler error: "
                        f"{error}"
                    )
                self._stop_event.wait(self.CHECK_INTERVAL)
        finally:
            if self.is_owner:
                self.runtime_lock.release()
                self.is_owner = False

    def run_due_jobs(self):
        now = datetime.now()
        jobs = self.store.load_all()

        for job in jobs:
            if not job.enabled or not job.next_run:
                continue

            try:
                due_time = datetime.fromisoformat(job.next_run)
            except ValueError:
                job.enabled = False
                job.mark_run("invalid_schedule")
                self.store.save(job)
                self._record_job_history(
                    job=job,
                    status="invalid_schedule",
                    error="Scheduled run time could not be parsed."
                )
                continue

            if due_time > now:
                continue

            try:
                self._run_job(job)
            except Exception as error:
                job.mark_run("failed", str(error))
                self.store.save(job)
                self._record_job_history(
                    job=job,
                    status="failed",
                    error=str(error)
                )
                print(
                    "Aether Scheduler: "
                    f"{job.job_id} isolated failure.\n"
                    f"{error}"
                )

    def _run_job(self, job):
        if job.recurrence == "daily":
            previous_due = datetime.fromisoformat(job.next_run)
            next_run = previous_due + timedelta(days=1)
            while next_run <= datetime.now():
                next_run += timedelta(days=1)
            job.next_run = next_run.isoformat(timespec="seconds")
        else:
            job.enabled = False
            job.next_run = None

        job.touch()
        self.store.save(job)

        print("\n" + "=" * 50)
        print("Aether Scheduler: " f"Running {job.job_id}")
        print(f"Goal: {job.goal}")
        print("=" * 50)

        workflow_message = "workflow " + job.workflow_request

        try:
            response = self.skill_manager.handle(workflow_message)
        except Exception as error:
            job.mark_run("failed", str(error))
            self.store.save(job)
            self._record_job_history(
                job=job,
                status="failed",
                error=str(error)
            )
            print(
                "Aether Scheduler: Job failed.\n"
                f"{error}"
            )
            return

        status = self._response_status(response)
        workflow_id = self._workflow_id_from_response(response)

        workflow = (
            self.workflow_store.get(workflow_id)
            if workflow_id
            else None
        )

        observability = None
        recovery_activity = None

        if workflow is not None:
            observability = self.workflow_observer.snapshot(workflow)
            recovery_activity = self.workflow_observer.summary(workflow)

            workflow_status = str(
                getattr(workflow, "status", "") or ""
            ).lower()

            if workflow_status in ("paused", "failed", "completed"):
                status = workflow_status

        job.mark_run(status, response)
        self.store.save(job)

        self._record_job_history(
            job=job,
            status=status,
            workflow_id=workflow_id,
            observability=observability,
            recovery_activity=recovery_activity
        )

        print(
            response
            or "Aether Scheduler: Job returned no response."
        )

        if recovery_activity:
            print(
                "\nAether Scheduler: "
                + recovery_activity
            )

        if status == "paused":
            print(
                "\nAether Scheduler: "
                "Workflow paused for permission. "
                "Background execution will not approve "
                "or bypass the permission request."
            )

        print(
            "\nAether Scheduler: "
            f"{job.job_id} -> {status}"
        )

    def _workflow_id_from_response(self, response):
        text = str(response or "")
        match = re.search(
            r"(?im)^ID:\s*([^\s]+)\s*$",
            text
        )
        if match is None:
            return None
        return match.group(1).strip()

    def _record_job_history(
        self,
        job,
        status,
        workflow_id=None,
        observability=None,
        recovery_activity=None,
        error=None
    ):
        try:
            self.job_history.record(
                job_id=str(
                    getattr(job, "job_id", "") or ""
                ),
                status=status,
                workflow_id=workflow_id,
                observability=observability,
                recovery_activity=recovery_activity,
                error=error
            )
        except OSError:
            pass

    def _response_status(self, response):
        text = str(response or "").lower()

        if "workflow status: paused" in text:
            return "paused"
        if "workflow status: failed" in text:
            return "failed"
        if "workflow status: completed" in text:
            return "completed"
        return "unknown"
