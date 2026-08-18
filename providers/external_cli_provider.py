import shutil
import subprocess

from providers.base_provider import BaseProvider


class ExternalCLIProvider(BaseProvider):
    """
    Generic adapter for external command-line tools.

    This provider can wrap installed CLIs and expose
    them to Aether through the standard provider API.
    """

    name = "external_cli"

    description = (
        "Generic adapter for external command-line tools."
    )

    def __init__(
        self,
        provider_name,
        executable,
        capabilities=None,
        description=None
    ):

        self.name = provider_name

        self.executable = executable

        self._capabilities = (
            capabilities
            if isinstance(
                capabilities,
                list
            )
            else []
        )

        if description:

            self.description = (
                description
            )

    # ---------------------------------
    # AVAILABLE
    # ---------------------------------

    def available(self):

        return (
            shutil.which(
                self.executable
            )
            is not None
        )

    # ---------------------------------
    # CAPABILITIES
    # ---------------------------------

    def capabilities(self):

        return list(
            self._capabilities
        )

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        capability,
        task
    ):

        if capability not in self._capabilities:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f'Capability "{capability}" '
                    "is not supported."
                )
            }

        if not self.available():

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f'Executable "{self.executable}" '
                    "is not available."
                )
            }

        if isinstance(
            task,
            dict
        ):

            args = task.get(
                "args",
                []
            )

            timeout = task.get(
                "timeout",
                120
            )

        else:

            args = [
                str(
                    task
                )
            ]

            timeout = 120

        if not isinstance(
            args,
            list
        ):

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "External provider arguments "
                    "must be a list."
                )
            }

        command = [
            self.executable
        ]

        command.extend(
            str(item)
            for item in args
        )

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False
            )

        except subprocess.TimeoutExpired:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f"{self.name} timed out."
                )
            }

        except (
            FileNotFoundError,
            OSError,
            subprocess.SubprocessError
        ) as error:

            return {
                "success": False,
                "provider": self.name,
                "error": str(
                    error
                )
            }

        return {
            "success": (
                result.returncode
                == 0
            ),
            "provider": self.name,
            "capability": capability,
            "returncode": (
                result.returncode
            ),
            "stdout": (
                result.stdout
                .strip()
            ),
            "stderr": (
                result.stderr
                .strip()
            )
        }
