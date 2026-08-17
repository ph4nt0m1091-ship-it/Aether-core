import os
import subprocess
from pathlib import Path

from providers.base_provider import BaseProvider


class LocalSystemProvider(BaseProvider):
    """
    Provides safe local Windows system capabilities.

    Initial capabilities:
    - Open approved applications
    - Open files/folders
    - List running processes

    More sensitive capabilities such as arbitrary
    command execution will be added behind Aether's
    permission layer.
    """

    name = "local_system"

    description = (
        "Controls approved applications and "
        "local Windows resources."
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

    # ---------------------------------
    # PROVIDER STATUS
    # ---------------------------------

    def available(self):
        """
        Return True when running on Windows.
        """

        return os.name == "nt"

    # ---------------------------------
    # CAPABILITIES
    # ---------------------------------

    def capabilities(self):
        """
        Return capabilities provided by this provider.
        """

        return [
            "open_app",
            "open_path",
            "list_processes"
        ]

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        capability,
        task
    ):
        """
        Route a capability request to the correct action.
        """

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
        """
        Open an application from Aether's approved list.
        """

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
    # OPEN FILE OR FOLDER
    # ---------------------------------

    def _open_path(self, task):
        """
        Open an existing file or folder using Windows.
        """

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
        """
        Read the currently running Windows processes.
        """

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

            if not parts:

                continue

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