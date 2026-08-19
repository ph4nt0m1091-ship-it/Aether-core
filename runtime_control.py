import os
import subprocess
import sys
import time

from pathlib import Path


BASE_DIR = Path(
    __file__
).resolve().parent

STORAGE_DIR = (
    BASE_DIR
    / "storage"
)

PID_PATH = (
    STORAGE_DIR
    / "background_runtime.pid"
)

RUNTIME_PATH = (
    BASE_DIR
    / "background_runtime.py"
)

PYTHON_PATH = Path(
    r"C:\Users\juju and bobby\AppData\Local\Programs\Python\Python311\python.exe"
)


# ---------------------------------
# READ PID
# ---------------------------------

def read_pid():

    if not PID_PATH.exists():

        return None

    try:

        text = (
            PID_PATH
            .read_text(
                encoding="utf-8"
            )
            .strip()
        )

        return int(
            text
        )

    except (
        OSError,
        ValueError
    ):

        return None


# ---------------------------------
# PROCESS EXISTS
# ---------------------------------

def process_exists(
    pid
):

    if not pid:

        return False

    try:

        result = subprocess.run(
            [
                "tasklist",
                "/FI",
                f"PID eq {pid}",
                "/FO",
                "CSV",
                "/NH"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

    except (
        OSError,
        subprocess.SubprocessError
    ):

        return False

    output = (
        result.stdout
        .strip()
        .lower()
    )

    if not output:

        return False

    if (
        "no tasks are running"
        in output
    ):

        return False

    return (
        f'"{pid}"'
        in output
    )


# ---------------------------------
# CLEAN STALE PID
# ---------------------------------

def cleanup_stale_pid():

    pid = read_pid()

    if (
        pid is not None
        and not process_exists(
            pid
        )
    ):

        try:

            PID_PATH.unlink(
                missing_ok=True
            )

        except OSError:

            pass

        return None

    return pid


# ---------------------------------
# STATUS
# ---------------------------------

def status():

    pid = cleanup_stale_pid()

    if (
        pid is not None
        and process_exists(
            pid
        )
    ):

        print(
            "Aether background runtime: running"
        )

        print(
            f"PID: {pid}"
        )

        return 0

    print(
        "Aether background runtime: stopped"
    )

    return 1


# ---------------------------------
# START
# ---------------------------------

def start():

    existing_pid = (
        cleanup_stale_pid()
    )

    if (
        existing_pid is not None
        and process_exists(
            existing_pid
        )
    ):

        print(
            "Aether background runtime "
            "is already running."
        )

        print(
            f"PID: {existing_pid}"
        )

        return 0

    if not PYTHON_PATH.exists():

        print(
            "Python executable was not found:"
        )

        print(
            PYTHON_PATH
        )

        return 1

    if not RUNTIME_PATH.exists():

        print(
            "background_runtime.py "
            "was not found."
        )

        return 1

    creation_flags = 0

    if os.name == "nt":

        creation_flags = (
            subprocess.CREATE_NO_WINDOW
            | subprocess.DETACHED_PROCESS
        )

    try:

        subprocess.Popen(
            [
                str(
                    PYTHON_PATH
                ),
                str(
                    RUNTIME_PATH
                )
            ],
            cwd=str(
                BASE_DIR
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
            close_fds=True
        )

    except OSError as error:

        print(
            "Failed to start Aether "
            "background runtime:"
        )

        print(
            error
        )

        return 1

    # Give background_runtime.py time
    # to create its PID file.

    for _ in range(
        20
    ):

        time.sleep(
            0.25
        )

        pid = read_pid()

        if (
            pid is not None
            and process_exists(
                pid
            )
        ):

            print(
                "Aether background runtime started."
            )

            print(
                f"PID: {pid}"
            )

            return 0

    print(
        "Aether background runtime "
        "did not confirm startup."
    )

    return 1


# ---------------------------------
# STOP
# ---------------------------------

def stop():

    pid = cleanup_stale_pid()

    if pid is None:

        print(
            "Aether background runtime "
            "is already stopped."
        )

        return 0

    try:

        result = subprocess.run(
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
    ) as error:

        print(
            "Failed to stop Aether "
            "background runtime:"
        )

        print(
            error
        )

        return 1

    # Give Windows time to remove
    # the terminated process.

    for _ in range(
        20
    ):

        time.sleep(
            0.25
        )

        if not process_exists(
            pid
        ):

            try:

                PID_PATH.unlink(
                    missing_ok=True
                )

            except OSError:

                pass

            print(
                "Aether background runtime stopped."
            )

            return 0

    print(
        "Aether background runtime "
        "did not stop cleanly."
    )

    if result.stderr:

        print(
            result.stderr.strip()
        )

    return 1


# ---------------------------------
# RESTART
# ---------------------------------

def restart():

    stop()

    time.sleep(
        0.5
    )

    return start()


# ---------------------------------
# HELP
# ---------------------------------

def help_text():

    print(
        "Aether Runtime Control\n"
    )

    print(
        "Usage:"
    )

    print(
        "  python runtime_control.py status"
    )

    print(
        "  python runtime_control.py start"
    )

    print(
        "  python runtime_control.py stop"
    )

    print(
        "  python runtime_control.py restart"
    )


# ---------------------------------
# MAIN
# ---------------------------------

def main():

    if len(
        sys.argv
    ) < 2:

        help_text()

        return 1

    command = (
        sys.argv[1]
        .strip()
        .lower()
    )

    if command == "status":

        return status()

    if command == "start":

        return start()

    if command == "stop":

        return stop()

    if command == "restart":

        return restart()

    help_text()

    return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )