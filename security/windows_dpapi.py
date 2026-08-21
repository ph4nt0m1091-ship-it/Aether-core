import ctypes
import os

from ctypes import wintypes


class DATA_BLOB(
    ctypes.Structure
):

    _fields_ = [
        (
            "cbData",
            wintypes.DWORD
        ),
        (
            "pbData",
            ctypes.POINTER(
                ctypes.c_byte
            )
        )
    ]


class WindowsDPAPI:
    """
    Small Windows DPAPI wrapper for Aether.

    Secrets encrypted here are protected using
    the current Windows user's credentials.

    No encryption key is stored in Aether.
    """

    CRYPTPROTECT_UI_FORBIDDEN = (
        0x01
    )

    def __init__(
        self
    ):

        if os.name != "nt":

            raise RuntimeError(
                "Windows DPAPI is only "
                "available on Windows."
            )

        self.crypt32 = (
            ctypes.windll.crypt32
        )

        self.kernel32 = (
            ctypes.windll.kernel32
        )

    # ---------------------------------
    # BLOB
    # ---------------------------------

    def _make_blob(
        self,
        data
    ):

        buffer = (
            ctypes.create_string_buffer(
                data,
                len(data)
            )
        )

        blob = DATA_BLOB(
            len(data),
            ctypes.cast(
                buffer,
                ctypes.POINTER(
                    ctypes.c_byte
                )
            )
        )

        return (
            blob,
            buffer
        )

    # ---------------------------------
    # PROTECT
    # ---------------------------------

    def protect(
        self,
        plaintext
    ):

        if isinstance(
            plaintext,
            str
        ):

            plaintext = (
                plaintext.encode(
                    "utf-8"
                )
            )

        if not isinstance(
            plaintext,
            bytes
        ):

            raise TypeError(
                "Secret must be text or bytes."
            )

        input_blob, input_buffer = (
            self._make_blob(
                plaintext
            )
        )

        output_blob = DATA_BLOB()

        result = (
            self.crypt32
            .CryptProtectData(
                ctypes.byref(
                    input_blob
                ),
                "Aether Secret",
                None,
                None,
                None,
                self.CRYPTPROTECT_UI_FORBIDDEN,
                ctypes.byref(
                    output_blob
                )
            )
        )

        # Keep input buffer alive through
        # CryptProtectData.
        _ = input_buffer

        if not result:

            raise ctypes.WinError()

        try:

            encrypted = (
                ctypes.string_at(
                    output_blob.pbData,
                    output_blob.cbData
                )
            )

        finally:

            self.kernel32.LocalFree(
                output_blob.pbData
            )

        return encrypted

    # ---------------------------------
    # UNPROTECT
    # ---------------------------------

    def unprotect(
        self,
        encrypted
    ):

        if not isinstance(
            encrypted,
            bytes
        ):

            raise TypeError(
                "Encrypted secret must be bytes."
            )

        input_blob, input_buffer = (
            self._make_blob(
                encrypted
            )
        )

        output_blob = DATA_BLOB()

        result = (
            self.crypt32
            .CryptUnprotectData(
                ctypes.byref(
                    input_blob
                ),
                None,
                None,
                None,
                None,
                self.CRYPTPROTECT_UI_FORBIDDEN,
                ctypes.byref(
                    output_blob
                )
            )
        )

        _ = input_buffer

        if not result:

            raise ctypes.WinError()

        try:

            plaintext = (
                ctypes.string_at(
                    output_blob.pbData,
                    output_blob.cbData
                )
            )

        finally:

            self.kernel32.LocalFree(
                output_blob.pbData
            )

        return plaintext.decode(
            "utf-8"
        )