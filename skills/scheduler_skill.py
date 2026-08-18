import re

from datetime import datetime, timedelta

from planner import Planner
from scheduled_job import ScheduledJob
from scheduler_engine import SchedulerEngine


class SchedulerSkill:
    """
    Persistent scheduling interface for Aether.

    Supported examples:

    schedule open notepad at 8:00 PM

    schedule research robotics news and save me
    a report at 9:00 AM

    schedule research robotics news and save me
    a report every day at 9:00 AM

    show scheduled jobs

    cancel scheduled job job_xxxxx

    disable scheduled job job_xxxxx

    enable scheduled job job_xxxxx
    """

    name = "scheduler"

    description = (
        "Schedules persistent one-time and daily "
        "Aether jobs for designated times."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.skill_manager = None

        self.engine = None

        self.planner = (
            Planner()
        )

    # ---------------------------------
    # CONNECT
    # ---------------------------------

    def connect(
        self,
        skill_manager
    ):

        self.skill_manager = (
            skill_manager
        )

        self.engine = SchedulerEngine(
            skill_manager
        )

    # ---------------------------------
    # START / STOP
    # ---------------------------------

    def start(
        self
    ):

        if self.engine is None:

            return False

        return self.engine.start()

    def stop(
        self
    ):

        if self.engine is not None:

            self.engine.stop()

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        message = message.strip()
        lower = message.lower()

        # ---------------------------------
        # SHOW JOBS
        # ---------------------------------

        if lower in (
            "show scheduled jobs",
            "list scheduled jobs",
            "show schedules",
            "show scheduler"
        ):

            return self._show_jobs()

        # ---------------------------------
        # CANCEL
        # ---------------------------------

        match = re.match(
            r"^cancel\s+scheduled\s+job\s+"
            r"(job_[a-zA-Z0-9]+)$",
            message,
            re.IGNORECASE
        )

        if match:

            return self._cancel_job(
                match.group(1)
            )

        # ---------------------------------
        # DISABLE
        # ---------------------------------

        match = re.match(
            r"^disable\s+scheduled\s+job\s+"
            r"(job_[a-zA-Z0-9]+)$",
            message,
            re.IGNORECASE
        )

        if match:

            return self._set_enabled(
                match.group(1),
                False
            )

        # ---------------------------------
        # ENABLE
        # ---------------------------------

        match = re.match(
            r"^enable\s+scheduled\s+job\s+"
            r"(job_[a-zA-Z0-9]+)$",
            message,
            re.IGNORECASE
        )

        if match:

            return self._set_enabled(
                match.group(1),
                True
            )

        # ---------------------------------
        # CREATE
        # ---------------------------------

        if lower.startswith(
            "schedule "
        ):

            return self._schedule(
                message[
                    len("schedule "):
                ].strip()
            )

        return None

    # ---------------------------------
    # CREATE JOB
    # ---------------------------------

    def _schedule(
        self,
        request
    ):

        parsed = self._parse_schedule(
            request
        )

        if not parsed.get(
            "success"
        ):

            return (
                "Aether: I couldn't understand "
                "that schedule.\n"
                f"{parsed.get('error', '')}"
            ).rstrip()

        goal = parsed[
            "goal"
        ]

        workflow_request = (
            self._build_workflow_request(
                goal
            )
        )

        if not workflow_request:

            return (
                "Aether: I couldn't build "
                "a workflow for that scheduled job."
            )

        job = ScheduledJob(
            goal=goal,
            workflow_request=(
                workflow_request
            ),
            next_run=(
                parsed["next_run"]
            ),
            recurrence=(
                parsed["recurrence"]
            )
        )

        self.engine.store.save(
            job
        )

        run_time = (
            datetime.fromisoformat(
                job.next_run
            )
        )

        recurrence_text = (
            "daily"
            if job.recurrence == "daily"
            else "one time"
        )

        return (
            "Aether: Scheduled job created.\n\n"
            f"ID: {job.job_id}\n"
            f"Goal: {job.goal}\n"
            f"Run: "
            f"{run_time.strftime('%Y-%m-%d %I:%M %p')}\n"
            f"Recurrence: "
            f"{recurrence_text}"
        )

    # ---------------------------------
    # PARSE SCHEDULE
    # ---------------------------------

    def _parse_schedule(
        self,
        request
    ):

        text = request.strip()

        recurrence = "once"

        daily_match = re.search(
            r"\s+every\s+day\s+at\s+"
            r"(\d{1,2})"
            r"(?::(\d{2}))?"
            r"\s*(am|pm)?\s*$",
            text,
            re.IGNORECASE
        )

        if daily_match:

            recurrence = "daily"

            goal = text[
                :daily_match.start()
            ].strip(
                " ,."
            )

            hour_text = (
                daily_match.group(1)
            )

            minute_text = (
                daily_match.group(2)
            )

            meridiem = (
                daily_match.group(3)
            )

        else:

            time_match = re.search(
                r"\s+at\s+"
                r"(\d{1,2})"
                r"(?::(\d{2}))?"
                r"\s*(am|pm)?\s*$",
                text,
                re.IGNORECASE
            )

            if not time_match:

                return {
                    "success": False,
                    "error": (
                        "Use a time such as "
                        '"at 8:00 PM" or '
                        '"every day at 9:00 AM".'
                    )
                }

            goal = text[
                :time_match.start()
            ].strip(
                " ,."
            )

            hour_text = (
                time_match.group(1)
            )

            minute_text = (
                time_match.group(2)
            )

            meridiem = (
                time_match.group(3)
            )

        if not goal:

            return {
                "success": False,
                "error": (
                    "No job goal was provided."
                )
            }

        try:

            hour = int(
                hour_text
            )

            minute = int(
                minute_text
                or "0"
            )

        except ValueError:

            return {
                "success": False,
                "error": (
                    "The schedule time is invalid."
                )
            }

        if minute < 0 or minute > 59:

            return {
                "success": False,
                "error": (
                    "Minutes must be between "
                    "00 and 59."
                )
            }

        if meridiem:

            meridiem = (
                meridiem.lower()
            )

            if hour < 1 or hour > 12:

                return {
                    "success": False,
                    "error": (
                        "12-hour times must use "
                        "hours 1 through 12."
                    )
                }

            if meridiem == "am":

                if hour == 12:

                    hour = 0

            elif meridiem == "pm":

                if hour != 12:

                    hour += 12

        else:

            if hour < 0 or hour > 23:

                return {
                    "success": False,
                    "error": (
                        "24-hour times must use "
                        "hours 0 through 23."
                    )
                }

        now = datetime.now()

        next_run = now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

        if next_run <= now:

            next_run += timedelta(
                days=1
            )

        return {
            "success": True,
            "goal": goal,
            "next_run": (
                next_run.isoformat(
                    timespec="seconds"
                )
            ),
            "recurrence": recurrence
        }

    # ---------------------------------
    # BUILD WORKFLOW
    # ---------------------------------

    def _build_workflow_request(
        self,
        goal
    ):

        lower = goal.lower()

        # Explicit workflow body.
        if lower.startswith(
            "workflow "
        ):

            return goal[
                len("workflow "):
            ].strip()

        # Already-canonical single-step actions.
        direct_prefixes = (
            "open ",
            "research ",
            "ask ollama ",
            "run ",
            "execute ",
            "terminal ",
            "search ",
            "look up ",
            "show providers",
            "show running processes"
        )

        if lower.startswith(
            direct_prefixes
        ):

            # Natural research goals may contain
            # additional requested actions.
            if (
                lower.startswith(
                    "research "
                )
                and self.planner
                .should_orchestrate(
                    goal
                )
            ):

                plan = (
                    self.planner
                    .create_workflow_request(
                        goal
                    )
                )

                if plan.get(
                    "success"
                ):

                    return plan.get(
                        "workflow_request"
                    )

            return goal

        # Higher-level natural language goal.
        plan = (
            self.planner
            .create_workflow_request(
                goal
            )
        )

        if plan.get(
            "success"
        ):

            return plan.get(
                "workflow_request"
            )

        return None

    # ---------------------------------
    # SHOW
    # ---------------------------------

    def _show_jobs(
        self
    ):

        jobs = (
            self.engine
            .store
            .load_all()
        )

        if not jobs:

            return (
                "Aether: No scheduled "
                "jobs found."
            )

        output = (
            "Aether: Scheduled Jobs\n\n"
        )

        jobs.sort(
            key=lambda job: (
                job.next_run
                or "9999"
            )
        )

        for job in jobs:

            status = (
                "enabled"
                if job.enabled
                else "disabled"
            )

            output += (
                f"- {job.job_id}\n"
                f"  Goal: {job.goal}\n"
                f"  Status: {status}\n"
                f"  Recurrence: "
                f"{job.recurrence}\n"
            )

            if job.next_run:

                try:

                    run_time = (
                        datetime.fromisoformat(
                            job.next_run
                        )
                    )

                    output += (
                        "  Next run: "
                        f"{run_time.strftime('%Y-%m-%d %I:%M:%S %p')}\n"
                    )

                except ValueError:

                    output += (
                        "  Next run: invalid\n"
                    )

            else:

                output += (
                    "  Next run: none\n"
                )

            if job.last_status:

                output += (
                    "  Last status: "
                    f"{job.last_status}\n"
                )

            output += "\n"

        return output.rstrip()

    # ---------------------------------
    # CANCEL
    # ---------------------------------

    def _cancel_job(
        self,
        job_id
    ):

        removed = (
            self.engine
            .store
            .delete(
                job_id
            )
        )

        if not removed:

            return (
                f'Aether: Scheduled job '
                f'"{job_id}" was not found.'
            )

        return (
            "Aether: Scheduled job "
            f"{job_id} cancelled."
        )

    # ---------------------------------
    # ENABLE / DISABLE
    # ---------------------------------

    def _set_enabled(
        self,
        job_id,
        enabled
    ):

        job = (
            self.engine
            .store
            .get(
                job_id
            )
        )

        if job is None:

            return (
                f'Aether: Scheduled job '
                f'"{job_id}" was not found.'
            )

        job.enabled = bool(
            enabled
        )

        job.touch()

        self.engine.store.save(
            job
        )

        state = (
            "enabled"
            if enabled
            else "disabled"
        )

        return (
            f"Aether: Scheduled job "
            f"{job_id} {state}."
        )

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None