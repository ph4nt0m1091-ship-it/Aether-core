import os
import sys
import time

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

from memory import Memory
from brain import Brain

from runtime_state import (
    remove_heartbeat,
    write_heartbeat
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
    / "background_runtime.log"
)

PID_PATH = (
    STORAGE_DIR
    / "background_runtime.pid"
)

HEALTH_INTERVAL = 2.0


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
# SCHEDULER HEALTH
# ---------------------------------

def scheduler_alive(
    brain
):

    scheduler_skill = (
        brain.skill_manager
        .registry
        .scheduler_skill
    )

    engine = (
        scheduler_skill.engine
    )

    if engine is None:

        return False

    thread = getattr(
        engine,
        "_thread",
        None
    )

    return bool(
        thread is not None
        and thread.is_alive()
        and engine.is_owner
    )


def repair_scheduler(
    brain
):

    if scheduler_alive(
        brain
    ):

        return True

    print(
        "Aether Background Runtime: "
        "scheduler health check failed."
    )

    scheduler_skill = (
        brain.skill_manager
        .registry
        .scheduler_skill
    )

    started = (
        scheduler_skill.start()
    )

    if started:

        print(
            "Aether Background Runtime: "
            "scheduler recovered."
        )

        return True

    print(
        "Aether Background Runtime: "
        "scheduler recovery failed."
    )

    return False


# ---------------------------------
# RUNTIME
# ---------------------------------

def runtime():

    os.chdir(
        BASE_DIR
    )

    memory = Memory()

    brain = Brain(
        memory
    )

    scheduler_skill = (
        brain.skill_manager
        .registry
        .scheduler_skill
    )

    started = (
        scheduler_skill.start()
    )

    if not started:

        print(
            "Aether Background Runtime: "
            "another scheduler already owns "
            "the runtime lock."
        )

        return 0

    write_pid()

    write_heartbeat(
        os.getpid(),
        scheduler_alive=True
    )

    print(
        "=" * 50
    )

    print(
        "AETHER BACKGROUND RUNTIME"
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

            healthy = (
                repair_scheduler(
                    brain
                )
            )

            write_heartbeat(
                os.getpid(),
                scheduler_alive=healthy
            )

            time.sleep(
                HEALTH_INTERVAL
            )

    except KeyboardInterrupt:

        print(
            "\nAether Background Runtime: "
            "shutdown requested."
        )

    finally:

        brain.skill_manager.stop_background_services()

        remove_heartbeat()

        remove_pid()

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

                return runtime()

            except Exception as error:

                print(
                    "Aether Background Runtime "
                    "crashed:"
                )

                print(
                    repr(
                        error
                    )
                )

                remove_heartbeat()

                remove_pid()

                return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )