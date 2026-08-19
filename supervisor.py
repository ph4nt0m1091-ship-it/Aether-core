import os
import subprocess
import sys
import time

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

import runtime_control

from runtime_lock import RuntimeLock
from runtime_state import (
    get_desired_state,
    heartbeat_age
)


BASE_DIR = Path(
    __file__
).resolve().parent

STORAGE_DIR = (
    BASE_DIR
    / "storage"
)

LOG_PATH = (
    STORAGE_DIR
    / "supervisor.log"
)

PID_PATH = (
    STORAGE_DIR
    / "supervisor.pid"
)

CHECK_INTERVAL = 5.0
HEARTBEAT_TIMEOUT = 15.0


# ---------------------------------
# PID
# ---------------------------------

def write_pid():

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    PID_PATH.write_text(
        str(
            os.getpid()
        ),
        encoding="utf-8"
    )


def remove_pid():

    try:

        PID_PATH.unlink(
            missing_ok=True
        )

    except OSError:

        pass


# ---------------------------------
# FORCE TERMINATE STALE RUNTIME
# ---------------------------------

def terminate_runtime(
    pid
):

    if not pid:

        return

    try:

        subprocess.run(
            [
                "taskkill",
                "/PID",
                str(
                    pid
                ),
                "/T",
                "/F"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

    except (
        OSError,
        subprocess.SubprocessError
    ):

        pass


# ---------------------------------
# HEALTH CHECK
# ---------------------------------

def ensure_runtime():

    desired = (
        get_desired_state()
    )

    pid = (
        runtime_control
        .cleanup_stale_pid()
    )

    running = (
        pid is not None
        and runtime_control
        .process_exists(
            pid
        )
    )

    # Respect an intentional shutdown.
    if desired == "stopped":

        return

    # Runtime should be running, but the
    # process has disappeared.
    if not running:

        print(
            "Aether Supervisor: "
            "background runtime is missing."
        )

        result = (
            runtime_control.start()
        )

        if result == 0:

            print(
                "Aether Supervisor: "
                "background runtime recovered."
            )

        else:

            print(
                "Aether Supervisor: "
                "background runtime recovery failed."
            )

        return

    age = heartbeat_age()

    # A newly started runtime may not have
    # written its first heartbeat yet.
    if age is None:

        return

    if age <= HEARTBEAT_TIMEOUT:

        return

    print(
        "Aether Supervisor: "
        "heartbeat is stale "
        f"({age:.1f} seconds)."
    )

    terminate_runtime(
        pid
    )

    time.sleep(
        1
    )

    runtime_control.cleanup_stale_pid()

    result = (
        runtime_control.start()
    )

    if result == 0:

        print(
            "Aether Supervisor: "
            "unresponsive runtime restarted."
        )

    else:

        print(
            "Aether Supervisor: "
            "runtime restart failed."
        )


# ---------------------------------
# SUPERVISOR
# ---------------------------------

def supervisor():

    os.chdir(
        BASE_DIR
    )

    lock = RuntimeLock(
        "storage/supervisor_runtime.lock"
    )

    if not lock.acquire():

        print(
            "Aether Supervisor: "
            "another supervisor is already running."
        )

        return 0

    write_pid()

    print(
        "=" * 50
    )

    print(
        "AETHER SUPERVISOR"
    )

    print(
        "Started: "
        + datetime.now().isoformat(
            timespec="seconds"
        )
    )

    print(
        "PID: "
        + str(
            os.getpid()
        )
    )

    print(
        "=" * 50
    )

    try:

        while True:

            try:

                ensure_runtime()

            except Exception as error:

                print(
                    "Aether Supervisor error: "
                    f"{error}"
                )

            time.sleep(
                CHECK_INTERVAL
            )

    except KeyboardInterrupt:

        print(
            "\nAether Supervisor: "
            "shutdown requested."
        )

    finally:

        remove_pid()

        lock.release()

    return 0


# ---------------------------------
# MAIN
# ---------------------------------

def main():

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with LOG_PATH.open(
        "a",
        encoding="utf-8",
        buffering=1
    ) as log_file:

        with redirect_stdout(
            log_file
        ), redirect_stderr(
            log_file
        ):

            try:

                return supervisor()

            except Exception as error:

                print(
                    "Aether Supervisor crashed:"
                )

                print(
                    repr(
                        error
                    )
                )

                remove_pid()

                return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )