import time
from collections import deque


class CloudRequestGuard:
    """
    Local cloud execution rate guard.

    This guard exists to prevent accidental
    runaway cloud execution.

    It does not replace:
    - privacy checks
    - user permission
    - provider cost controls

    It runs immediately before network execution.
    """

    def __init__(
        self,
        max_requests=5,
        window_seconds=60
    ):

        self.max_requests = int(
            max_requests
        )

        self.window_seconds = int(
            window_seconds
        )

        self.request_times = deque()

    # ---------------------------------
    # CLEAN OLD EVENTS
    # ---------------------------------

    def _cleanup(
        self,
        now=None
    ):

        if now is None:

            now = time.monotonic()

        cutoff = (
            now
            - self.window_seconds
        )

        while (
            self.request_times
            and self.request_times[0]
            <= cutoff
        ):

            self.request_times.popleft()

    # ---------------------------------
    # CAN SEND
    # ---------------------------------

    def can_send(
        self
    ):

        now = time.monotonic()

        self._cleanup(
            now
        )

        allowed = (
            len(
                self.request_times
            )
            < self.max_requests
        )

        retry_after = 0

        if (
            not allowed
            and self.request_times
        ):

            retry_after = max(
                1,
                int(
                    self.window_seconds
                    - (
                        now
                        - self.request_times[0]
                    )
                )
                + 1
            )

        return {
            "allowed": allowed,
            "current_requests": len(
                self.request_times
            ),
            "max_requests": (
                self.max_requests
            ),
            "window_seconds": (
                self.window_seconds
            ),
            "retry_after_seconds": (
                retry_after
            )
        }

    # ---------------------------------
    # RECORD SEND
    # ---------------------------------

    def record_send(
        self
    ):

        now = time.monotonic()

        self._cleanup(
            now
        )

        self.request_times.append(
            now
        )

        return self.status()

    # ---------------------------------
    # STATUS
    # ---------------------------------

    def status(
        self
    ):

        state = (
            self.can_send()
        )

        return {
            "allowed": (
                state["allowed"]
            ),
            "current_requests": (
                state[
                    "current_requests"
                ]
            ),
            "max_requests": (
                self.max_requests
            ),
            "window_seconds": (
                self.window_seconds
            ),
            "retry_after_seconds": (
                state[
                    "retry_after_seconds"
                ]
            )
        }

    # ---------------------------------
    # RESET
    # ---------------------------------

    def reset(
        self
    ):

        self.request_times.clear()

        return True