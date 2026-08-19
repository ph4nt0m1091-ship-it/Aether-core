import json
import os

from datetime import datetime
from pathlib import Path


BASE_DIR = Path(
    __file__
).resolve().parent

STORAGE_DIR = (
    BASE_DIR
    / "storage"
)

STATE_PATH = (
    STORAGE_DIR
    / "runtime_state.json"
)

HEARTBEAT_PATH = (
    STORAGE_DIR
    / "background_heartbeat.json"
)


# ---------------------------------
# DESIRED STATE
# ---------------------------------

def get_desired_state():

    if not STATE_PATH.exists():

        return "running"

    try:

        data = json.loads(
            STATE_PATH.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError
    ):

        return "running"

    state = str(
        data.get(
            "desired_state",
            "running"
        )
    ).lower()

    if state not in (
        "running",
        "stopped"
    ):

        return "running"

    return state


def set_desired_state(
    state
):

    state = str(
        state
    ).strip().lower()

    if state not in (
        "running",
        "stopped"
    ):

        raise ValueError(
            "Runtime state must be "
            '"running" or "stopped".'
        )

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    data = {
        "desired_state": state,
        "updated_at": (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        )
    }

    _atomic_json_write(
        STATE_PATH,
        data
    )


# ---------------------------------
# HEARTBEAT
# ---------------------------------

def write_heartbeat(
    pid,
    scheduler_alive=True
):

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    data = {
        "pid": int(
            pid
        ),
        "timestamp": (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        ),
        "scheduler_alive": bool(
            scheduler_alive
        )
    }

    _atomic_json_write(
        HEARTBEAT_PATH,
        data
    )


def read_heartbeat():

    if not HEARTBEAT_PATH.exists():

        return None

    try:

        data = json.loads(
            HEARTBEAT_PATH.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError
    ):

        return None

    if not isinstance(
        data,
        dict
    ):

        return None

    return data


def heartbeat_age():

    data = read_heartbeat()

    if data is None:

        return None

    timestamp = data.get(
        "timestamp"
    )

    if not timestamp:

        return None

    try:

        heartbeat_time = (
            datetime.fromisoformat(
                timestamp
            )
        )

    except ValueError:

        return None

    return (
        datetime.now()
        - heartbeat_time
    ).total_seconds()


def remove_heartbeat():

    try:

        HEARTBEAT_PATH.unlink(
            missing_ok=True
        )

    except OSError:

        pass


# ---------------------------------
# ATOMIC JSON
# ---------------------------------

def _atomic_json_write(
    path,
    data
):

    temp_path = path.with_suffix(
        path.suffix
        + f".{os.getpid()}.tmp"
    )

    try:

        temp_path.write_text(
            json.dumps(
                data,
                indent=4
            ),
            encoding="utf-8"
        )

        temp_path.replace(
            path
        )

    finally:

        try:

            temp_path.unlink(
                missing_ok=True
            )

        except OSError:

            pass