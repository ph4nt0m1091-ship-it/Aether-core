from pathlib import Path


class RuntimeLock:
    """
    Cross-process file lock used to guarantee that
    only one Aether scheduler worker runs at a time.

    On Windows this uses msvcrt byte-range locking.
    """

    def __init__(
        self,
        path="storage/scheduler_runtime.lock"
    ):

        self.path = Path(
            path
        )

        self.handle = None

        self.acquired = False

    # ---------------------------------
    # ACQUIRE
    # ---------------------------------

    def acquire(
        self
    ):

        if self.acquired:

            return True

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.handle = self.path.open(
            "a+b"
        )

        self.handle.seek(
            0,
            2
        )

        if self.handle.tell() == 0:

            self.handle.write(
                b"\0"
            )

            self.handle.flush()

        self.handle.seek(
            0
        )

        try:

            import msvcrt

            msvcrt.locking(
                self.handle.fileno(),
                msvcrt.LK_NBLCK,
                1
            )

        except (
            ImportError,
            OSError
        ):

            self._close_handle()

            return False

        self.acquired = True

        return True

    # ---------------------------------
    # RELEASE
    # ---------------------------------

    def release(
        self
    ):

        if (
            not self.acquired
            or self.handle is None
        ):

            return

        try:

            import msvcrt

            self.handle.seek(
                0
            )

            msvcrt.locking(
                self.handle.fileno(),
                msvcrt.LK_UNLCK,
                1
            )

        except (
            ImportError,
            OSError
        ):

            pass

        self.acquired = False

        self._close_handle()

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def _close_handle(
        self
    ):

        if self.handle is not None:

            try:

                self.handle.close()

            except OSError:

                pass

        self.handle = None

    # ---------------------------------
    # CONTEXT MANAGER
    # ---------------------------------

    def __enter__(
        self
    ):

        if not self.acquire():

            raise RuntimeError(
                "Aether scheduler lock "
                "is already owned."
            )

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):

        self.release()