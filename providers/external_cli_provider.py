import os
import shutil
import subprocess

from pathlib import Path

from providers.base_provider import BaseProvider


class ExternalCLIProvider(BaseProvider):
    """
    Generic adapter for external command-line agents.

    Safety properties:
    - shell=False
    - fixed executable
    - structured arguments
    - explicit timeout
    - optional working directory
    - permission metadata
    - captures stdout/stderr
    """

    provider_type = "external_agent"

    requires_permission = True

    DEFAULT_TIMEOUT = 300

    def __init__(
        self,
        provider_name,
        executable,
        capabilities=None,
        description=None,
        default_args=None,
        working_directory=None
    ):

        self.name = str(
            provider_name
        ).strip()

        self.executable = str(
            executable
        ).strip()

        self._capabilities = (
            list(capabilities)
            if isinstance(
                capabilities,
                list
            )
            else []
        )

        self.default_args = (
            list(default_args)
            if isinstance(
                default_args,
                list
            )
            else []
        )

        self.working_directory = (
            str(working_directory)
            if working_directory
            else None
        )

        if description:

            self.description = str(
                description
            )

        else:

            self.description = (
                "External command-line agent."
            )

    # ---------------------------------
    # RESOLVE EXECUTABLE
    # ---------------------------------

    def executable_path(self):

        return shutil.which(
            self.executable
        )

    # ---------------------------------
    # AVAILABLE
    # ---------------------------------

    def available(self):

        return (
            self.executable_path()
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
    # INFO
    # ---------------------------------

    def info(self):

        data = super().info()

        data.update(
            {
                "executable": (
                    self.executable
                ),
                "executable_path": (
                    self.executable_path()
                ),
                "working_directory": (
                    self.working_directory
                )
            }
        )

        return data

    # ---------------------------------
    # PREVIEW COMMAND
    # ---------------------------------

    def preview_command(
        self,
        task
    ):

        args = list(
            self.default_args
        )

        if isinstance(
            task,
            dict
        ):

            task_args = task.get(
                "args",
                []
            )

            if isinstance(
                task_args,
                list
            ):

                args.extend(
                    str(item)
                    for item in task_args
                )

        elif task is not None:

            args.append(
                str(task)
            )

        return [
            self.executable
        ] + args

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
                "provider_type": (
                    self.provider_type
                ),
                "error": (
                    f'Capability "{capability}" '
                    "is not supported."
                )
            }

        executable_path = (
            self.executable_path()
        )

        if executable_path is None:

            return {
                "success": False,
                "provider": self.name,
                "provider_type": (
                    self.provider_type
                ),
                "error": (
                    f'Executable "{self.executable}" '
                    "is not available."
                )
            }

        if isinstance(
            task,
            dict
        ):

            task_args = task.get(
                "args",
                []
            )

            timeout = task.get(
                "timeout",
                self.DEFAULT_TIMEOUT
            )

            cwd = task.get(
                "cwd",
                self.working_directory
            )

        else:

            task_args = [
                str(task)
            ]

            timeout = (
                self.DEFAULT_TIMEOUT
            )

            cwd = (
                self.working_directory
            )

        if not isinstance(
            task_args,
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

        args = list(
            self.default_args
        )

        args.extend(
            str(item)
            for item in task_args
        )

        command = [
            executable_path
        ] + args

        creation_flags = 0

        if os.name == "nt":

            creation_flags = (
                subprocess.CREATE_NO_WINDOW
            )

        try:

            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
                creationflags=creation_flags
            )

        except subprocess.TimeoutExpired:

            return {
                "success": False,
                "provider": self.name,
                "provider_type": (
                    self.provider_type
                ),
                "capability": capability,
                "command": command,
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
                "provider_type": (
                    self.provider_type
                ),
                "capability": capability,
                "command": command,
                "error": str(
                    error
                )
            }

        stdout = (
            result.stdout
            .strip()
        )

        stderr = (
            result.stderr
            .strip()
        )

        return {
            "success": (
                result.returncode
                == 0
            ),
            "provider": self.name,
            "provider_type": (
                self.provider_type
            ),
            "capability": capability,
            "command": command,
            "cwd": cwd,
            "returncode": (
                result.returncode
            ),
            "stdout": stdout,
            "stderr": stderr,
            "response": stdout,
            "requires_permission": (
                self.requires_permission
            )
        }