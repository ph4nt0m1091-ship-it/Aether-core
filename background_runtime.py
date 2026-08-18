import os
import sys
import time

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

from memory import Memory
from brain import Brain


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


def runtime():

    os.chdir(
        BASE_DIR
    )

    memory = Memory()

    brain = Brain(
        memory
    )

    started = (
        brain.skill_manager
        .registry
        .scheduler_skill
        .start()
    )

    if not started:

        print(
            "Aether Background Runtime: "
            "another scheduler already owns "
            "the runtime lock."
        )

        return 0

    write_pid()

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

            time.sleep(
                1
            )

    except KeyboardInterrupt:

        print(
            "\nAether Background Runtime: "
            "shutdown requested."
        )

    finally:

        brain.skill_manager.stop_background_services()

        remove_pid()

    return 0


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

                remove_pid()

                return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )