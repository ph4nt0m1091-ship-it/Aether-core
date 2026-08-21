from pathlib import Path

from security.windows_dpapi import (
    WindowsDPAPI
)


class SecretStore:
    """
    Local encrypted secret storage for Aether.

    Secrets are stored under storage/secrets/
    and protected with Windows DPAPI.

    Secret values are never returned by status
    or listing methods.
    """

    def __init__(
        self,
        base_directory=None
    ):

        if base_directory is None:

            base_directory = (
                Path(__file__)
                .resolve()
                .parent
                .parent
            )

        self.base_directory = Path(
            base_directory
        )

        self.secret_directory = (
            self.base_directory
            / "storage"
            / "secrets"
        )

        self.secret_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        self.dpapi = (
            WindowsDPAPI()
        )

    # ---------------------------------
    # SAFE NAME
    # ---------------------------------

    def _safe_name(
        self,
        name
    ):

        name = str(
            name or ""
        ).strip().lower()

        allowed = (
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789_-"
        )

        cleaned = "".join(
            character
            for character in name
            if character in allowed
        )

        if (
            not cleaned
            or cleaned != name
        ):

            raise ValueError(
                "Invalid secret name."
            )

        return cleaned

    # ---------------------------------
    # PATH
    # ---------------------------------

    def _path(
        self,
        name
    ):

        name = (
            self._safe_name(
                name
            )
        )

        return (
            self.secret_directory
            / f"{name}.secret"
        )

    # ---------------------------------
    # SET
    # ---------------------------------

    def set(
        self,
        name,
        value
    ):

        value = str(
            value or ""
        )

        if not value:

            raise ValueError(
                "Secret value cannot be empty."
            )

        path = self._path(
            name
        )

        encrypted = (
            self.dpapi.protect(
                value
            )
        )

        path.write_bytes(
            encrypted
        )

        return True

    # ---------------------------------
    # GET
    # ---------------------------------

    def get(
        self,
        name
    ):

        path = self._path(
            name
        )

        if not path.exists():

            return None

        encrypted = (
            path.read_bytes()
        )

        return (
            self.dpapi.unprotect(
                encrypted
            )
        )

    # ---------------------------------
    # EXISTS
    # ---------------------------------

    def exists(
        self,
        name
    ):

        return (
            self._path(
                name
            ).exists()
        )

    # ---------------------------------
    # DELETE
    # ---------------------------------

    def delete(
        self,
        name
    ):

        path = self._path(
            name
        )

        if not path.exists():

            return False

        path.unlink()

        return True

    # ---------------------------------
    # STATUS
    # ---------------------------------

    def status(
        self,
        name
    ):

        return {
            "name": (
                self._safe_name(
                    name
                )
            ),
            "configured": (
                self.exists(
                    name
                )
            ),
            "encrypted": True,
            "storage": (
                "windows_dpapi"
            )
        }