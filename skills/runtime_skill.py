import io

from contextlib import redirect_stdout

import runtime_control


class RuntimeSkill:
    """
    Gives Aether awareness and control over its
    persistent background runtime.

    Supported commands:

    background status
    background start
    background stop
    background restart

    runtime status
    runtime start
    runtime stop
    runtime restart

    The skill coordinates scheduler ownership so
    the interactive process and background process
    do not fight for the scheduler runtime lock.
    """

    name = "runtime"

    description = (
        "Manages Aether's persistent background "
        "runtime and scheduler ownership."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.skill_manager = None

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
        # STATUS
        # ---------------------------------

        if lower in (
            "background status",
            "runtime status",
            "background runtime status",
            "show background status"
        ):

            return self._status()

        # ---------------------------------
        # START
        # ---------------------------------

        if lower in (
            "background start",
            "runtime start",
            "start background",
            "start background runtime"
        ):

            return self._start()

        # ---------------------------------
        # STOP
        # ---------------------------------

        if lower in (
            "background stop",
            "runtime stop",
            "stop background",
            "stop background runtime"
        ):

            return self._stop()

        # ---------------------------------
        # RESTART
        # ---------------------------------

        if lower in (
            "background restart",
            "runtime restart",
            "restart background",
            "restart background runtime"
        ):

            return self._restart()

        return None

    # ---------------------------------
    # STATUS
    # ---------------------------------

    def _status(
        self
    ):

        pid = (
            runtime_control
            .cleanup_stale_pid()
        )

        background_running = (
            pid is not None
            and runtime_control
            .process_exists(
                pid
            )
        )

        local_scheduler = (
            self._local_scheduler_owner()
        )

        output = (
            "Aether: Background Runtime Status\n\n"
        )

        if background_running:

            output += (
                "Background runtime: running\n"
                f"PID: {pid}\n"
            )

        else:

            output += (
                "Background runtime: stopped\n"
            )

        output += (
            "Interactive scheduler: "
            + (
                "active"
                if local_scheduler
                else "inactive"
            )
        )

        if background_running:

            output += (
                "\nScheduler owner: "
                "background runtime"
            )

        elif local_scheduler:

            output += (
                "\nScheduler owner: "
                "interactive Aether"
            )

        else:

            output += (
                "\nScheduler owner: none"
            )

        return output

    # ---------------------------------
    # START BACKGROUND
    # ---------------------------------

    def _start(
        self
    ):

        pid = (
            runtime_control
            .cleanup_stale_pid()
        )

        if (
            pid is not None
            and runtime_control
            .process_exists(
                pid
            )
        ):

            return (
                "Aether: Background runtime "
                "is already running.\n"
                f"PID: {pid}"
            )

        scheduler_skill = (
            self._scheduler_skill()
        )

        local_was_owner = (
            self._local_scheduler_owner()
        )

        # The background runtime needs the same
        # scheduler lock. If interactive Aether owns
        # it, release it before starting background.
        if (
            local_was_owner
            and scheduler_skill is not None
        ):

            scheduler_skill.stop()

        code, output = (
            self._capture(
                runtime_control.start
            )
        )

        if code == 0:

            pid = (
                runtime_control
                .cleanup_stale_pid()
            )

            result = (
                "Aether: Background runtime started."
            )

            if pid is not None:

                result += (
                    f"\nPID: {pid}"
                )

            result += (
                "\nScheduler ownership transferred "
                "to the background runtime."
            )

            return result

        # If background startup failed, restore
        # interactive scheduling so jobs are not
        # accidentally left without a worker.
        if (
            local_was_owner
            and scheduler_skill is not None
        ):

            scheduler_skill.start()

        return (
            "Aether: Background runtime "
            "could not be started.\n"
            + (
                output
                or "Unknown runtime error."
            )
        )

    # ---------------------------------
    # STOP BACKGROUND
    # ---------------------------------

    def _stop(
        self
    ):

        pid = (
            runtime_control
            .cleanup_stale_pid()
        )

        if pid is None:

            # Make sure interactive Aether owns the
            # scheduler if no background runtime exists.
            scheduler_skill = (
                self._scheduler_skill()
            )

            if (
                scheduler_skill is not None
                and not self._local_scheduler_owner()
            ):

                scheduler_skill.start()

            return (
                "Aether: Background runtime "
                "is already stopped.\n"
                "Interactive scheduling is available."
            )

        code, output = (
            self._capture(
                runtime_control.stop
            )
        )

        if code != 0:

            return (
                "Aether: Background runtime "
                "could not be stopped cleanly.\n"
                + (
                    output
                    or "Unknown runtime error."
                )
            )

        scheduler_skill = (
            self._scheduler_skill()
        )

        scheduler_started = False

        if scheduler_skill is not None:

            scheduler_started = (
                scheduler_skill.start()
            )

        result = (
            "Aether: Background runtime stopped."
        )

        if scheduler_started:

            result += (
                "\nScheduler ownership returned "
                "to interactive Aether."
            )

        else:

            result += (
                "\nInteractive scheduler was "
                "already active or unavailable."
            )

        return result

    # ---------------------------------
    # RESTART BACKGROUND
    # ---------------------------------

    def _restart(
        self
    ):

        pid = (
            runtime_control
            .cleanup_stale_pid()
        )

        # Stop the existing background runtime first.
        if (
            pid is not None
            and runtime_control
            .process_exists(
                pid
            )
        ):

            code, output = (
                self._capture(
                    runtime_control.stop
                )
            )

            if code != 0:

                return (
                    "Aether: Background runtime "
                    "could not be stopped for restart.\n"
                    + (
                        output
                        or "Unknown runtime error."
                    )
                )

        scheduler_skill = (
            self._scheduler_skill()
        )

        # Interactive Aether may have reclaimed
        # scheduler ownership after background stopped.
        if (
            scheduler_skill is not None
            and self._local_scheduler_owner()
        ):

            scheduler_skill.stop()

        code, output = (
            self._capture(
                runtime_control.start
            )
        )

        if code == 0:

            pid = (
                runtime_control
                .cleanup_stale_pid()
            )

            result = (
                "Aether: Background runtime restarted."
            )

            if pid is not None:

                result += (
                    f"\nPID: {pid}"
                )

            result += (
                "\nScheduler owner: "
                "background runtime"
            )

            return result

        # Restore local scheduler if restart failed.
        if scheduler_skill is not None:

            scheduler_skill.start()

        return (
            "Aether: Background runtime "
            "restart failed.\n"
            + (
                output
                or "Unknown runtime error."
            )
        )

    # ---------------------------------
    # SCHEDULER ACCESS
    # ---------------------------------

    def _scheduler_skill(
        self
    ):

        if self.skill_manager is None:

            return None

        return (
            self.skill_manager
            .registry
            .get_skill(
                "scheduler"
            )
        )

    def _local_scheduler_owner(
        self
    ):

        scheduler_skill = (
            self._scheduler_skill()
        )

        if (
            scheduler_skill is None
            or scheduler_skill.engine is None
        ):

            return False

        return bool(
            scheduler_skill
            .engine
            .is_owner
        )

    # ---------------------------------
    # CAPTURE RUNTIME CONTROL OUTPUT
    # ---------------------------------

    def _capture(
        self,
        function
    ):

        stream = io.StringIO()

        with redirect_stdout(
            stream
        ):

            code = function()

        return (
            code,
            stream.getvalue().strip()
        )

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None