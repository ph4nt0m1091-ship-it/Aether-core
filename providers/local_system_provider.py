import os
import shlex
import subprocess
from pathlib import Path

from providers.base_provider import BaseProvider


class LocalSystemProvider(BaseProvider):
    """
    Provides controlled local Windows capabilities.

    Capabilities:
    - Open approved applications
    - Open files/folders
    - List running processes
    - Run approved executable commands
    """

    name = "local_system"

    description = (
        "Controls approved applications, local resources, "
        "and permission-gated commands."
    )

    APP_ALIASES = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "paint": "mspaint.exe",
        "powershell": "powershell.exe",
        "terminal": "wt.exe",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",

        "vscode": (
            r"C:\Users\juju and bobby\AppData\Local"
            r"\Programs\Microsoft VS Code\Code.exe"
        ),

        "vs code": (
            r"C:\Users\juju and bobby\AppData\Local"
            r"\Programs\Microsoft VS Code\Code.exe"
        ),

        "visual studio code": (
            r"C:\Users\juju and bobby\AppData\Local"
            r"\Programs\Microsoft VS Code\Code.exe"
        )
    }

    APPROVED_EXECUTABLES = {
        "git",
        "git.exe",
        "python",
        "python.exe",
        "py",
        "py.exe",
        "where",
        "where.exe",
        "tasklist",
        "tasklist.exe",
        "ipconfig",
        "ipconfig.exe",
        "ping",
        "ping.exe"
    }

    def available(self):

        return os.name == "nt"

    def capabilities(self):

        return [
            "open_app",
            "open_path",
            "list_processes",
            "run_command"
        ]

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        capability,
        task
    ):

        if capability == "open_app":

            return self._open_app(
                task
            )

        if capability == "open_path":

            return self._open_path(
                task
            )

        if capability == "list_processes":

            return self._list_processes()

        if capability == "run_command":

            return self._run_command(
                task
            )

        return {
            "success": False,
            "provider": self.name,
            "error": (
                f'Unsupported capability: '
                f'"{capability}"'
            )
        }

    # ---------------------------------
    # OPEN APPLICATION
    # ---------------------------------

    def _open_app(self, task):

        if isinstance(
            task,
            dict
        ):

            app_name = task.get(
                "app",
                ""
            )

        else:

            app_name = str(
                task
            )

        app_name = (
            app_name
            .strip()
            .lower()
        )

        if not app_name:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "No application was provided."
                )
            }

        executable = self.APP_ALIASES.get(
            app_name
        )

        if executable is None:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f'Application "{app_name}" '
                    "is not in the approved app list."
                )
            }

        try:

            subprocess.Popen(
                [executable],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        except FileNotFoundError:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f'Application "{app_name}" '
                    "could not be found."
                )
            }

        except OSError as error:

            return {
                "success": False,
                "provider": self.name,
                "error": str(
                    error
                )
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "open_app",
            "application": app_name
        }

    # ---------------------------------
    # OPEN PATH
    # ---------------------------------

    def _open_path(self, task):

        if isinstance(
            task,
            dict
        ):

            raw_path = task.get(
                "path",
                ""
            )

        else:

            raw_path = str(
                task
            )

        raw_path = raw_path.strip()

        if not raw_path:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "No path was provided."
                )
            }

        path = Path(
            raw_path
        ).expanduser()

        if not path.exists():

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f"Path does not exist: "
                    f"{path}"
                )
            }

        try:

            os.startfile(
                str(path)
            )

        except OSError as error:

            return {
                "success": False,
                "provider": self.name,
                "error": str(
                    error
                )
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "open_path",
            "path": str(
                path
            )
        }

    # ---------------------------------
    # LIST PROCESSES
    # ---------------------------------

    def _list_processes(self):

        try:

            result = subprocess.run(
                [
                    "tasklist",
                    "/FO",
                    "CSV",
                    "/NH"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

        except (
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

        if result.returncode != 0:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    result.stderr.strip()
                    or "Unable to read processes."
                )
            }

        processes = []

        for line in result.stdout.splitlines():

            line = line.strip()

            if not line:

                continue

            parts = [
                item.strip(
                    '"'
                )
                for item in line.split(
                    '","'
                )
            ]

            processes.append(
                {
                    "name": parts[0],
                    "pid": (
                        parts[1]
                        if len(parts) > 1
                        else ""
                    )
                }
            )

        return {
            "success": True,
            "provider": self.name,
            "capability": "list_processes",
            "count": len(
                processes
            ),
            "processes": processes
        }

    # ---------------------------------
    # RUN COMMAND
    # ---------------------------------

    def _run_command(self, task):
        """
        Execute a command without using shell=True.

        CommandPolicy and PermissionManager are responsible
        for deciding whether execution is permitted.
        """

        if isinstance(
            task,
            dict
        ):

            command = task.get(
                "command",
                ""
            )

            cwd = task.get(
                "cwd"
            )

        else:

            command = str(
                task
            )

            cwd = None

        command = command.strip()

        if not command:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "No command was provided."
                )
            }

        try:

            parts = shlex.split(
                command,
                posix=False
            )

        except ValueError as error:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f"Unable to parse command: "
                    f"{error}"
                )
            }

        parts = [
            part.strip(
                "\"'"
            )
            for part in parts
        ]

        if not parts:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "No executable was found."
                )
            }

        executable = (
            Path(parts[0])
            .name
            .lower()
        )

        if executable not in self.APPROVED_EXECUTABLES:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f'Executable "{executable}" '
                    "is not approved."
                )
            }

        if cwd:

            working_directory = Path(
                cwd
            ).expanduser()

            if not working_directory.exists():

                return {
                    "success": False,
                    "provider": self.name,
                    "error": (
                        f"Working directory does not exist: "
                        f"{working_directory}"
                    )
                }

            working_directory = str(
                working_directory
            )

        else:

            working_directory = None

        try:

            result = subprocess.run(
                parts,
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=60,
                shell=False
            )

        except subprocess.TimeoutExpired:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "Command timed out after 60 seconds."
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
                result.returncode == 0
            ),
            "provider": self.name,
            "capability": "run_command",
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }