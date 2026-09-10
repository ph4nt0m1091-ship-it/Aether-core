import csv
import io
import json
import os
import shlex
import subprocess
from pathlib import Path

from providers.base_provider import BaseProvider


class LocalSystemProvider(BaseProvider):
    """
    Controlled local Windows capabilities.

    Low-risk desktop actions:
    - open approved applications
    - open existing paths / approved user folders
    - list processes and visible windows
    - check whether an approved app is running

    Command execution remains permission-aware.
    """

    name = "local_system"

    description = (
        "Controls approved applications, local resources, "
        "desktop inspection, and permission-gated commands."
    )

    APP_ALIASES = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "paint": "mspaint.exe",
        "powershell": "powershell.exe",
        "terminal": "wt.exe",
        "windows terminal": "wt.exe",
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

    FRIENDLY_APP_ALIASES = {
        "code": "vs code",
        "files": "file explorer"
    }

    KNOWN_FOLDERS = {
        "home": Path.home(),
        "user folder": Path.home(),
        "profile": Path.home(),
        "desktop": Path.home() / "Desktop",
        "documents": Path.home() / "Documents",
        "downloads": Path.home() / "Downloads",
        "pictures": Path.home() / "Pictures",
        "music": Path.home() / "Music",
        "videos": Path.home() / "Videos"
    }

    APPROVED_EXECUTABLES = {
        "git", "git.exe",
        "python", "python.exe",
        "py", "py.exe",
        "where", "where.exe",
        "tasklist", "tasklist.exe",
        "ipconfig", "ipconfig.exe",
        "ping", "ping.exe"
    }

    def available(self):
        return os.name == "nt"

    def capabilities(self):
        return [
            "open_app",
            "open_path",
            "open_known_folder",
            "list_processes",
            "list_windows",
            "is_app_running",
            "list_app_windows",
            "focus_app",
            "run_command"
        ]

    def execute(self, capability, task):
        if capability == "open_app":
            return self._open_app(task)
        if capability == "open_path":
            return self._open_path(task)
        if capability == "open_known_folder":
            return self._open_known_folder(task)
        if capability == "list_processes":
            return self._list_processes()
        if capability == "list_windows":
            return self._list_windows()
        if capability == "is_app_running":
            return self._is_app_running(task)
        if capability == "list_app_windows":
            return self._list_app_windows(task)
        if capability == "focus_app":
            return self._focus_app(task)
        if capability == "run_command":
            return self._run_command(task)
        return {
            "success": False,
            "provider": self.name,
            "error": f'Unsupported capability: "{capability}"'
        }

    def _normalize_app_name(self, app_name):
        normalized = str(app_name or "").strip().lower()
        return self.FRIENDLY_APP_ALIASES.get(
            normalized,
            normalized
        )

    def _open_app(self, task):
        if isinstance(task, dict):
            app_name = task.get("app", "")
        else:
            app_name = str(task)

        app_name = self._normalize_app_name(app_name)

        if not app_name:
            return {
                "success": False,
                "provider": self.name,
                "error": "No application was provided."
            }

        executable = self.APP_ALIASES.get(app_name)

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
                "error": str(error)
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "open_app",
            "application": app_name
        }

    def _open_path(self, task):
        if isinstance(task, dict):
            raw_path = task.get("path", "")
        else:
            raw_path = str(task)

        raw_path = str(raw_path or "").strip()

        if not raw_path:
            return {
                "success": False,
                "provider": self.name,
                "error": "No path was provided."
            }

        path = Path(raw_path).expanduser()

        if not path.exists():
            return {
                "success": False,
                "provider": self.name,
                "error": f"Path does not exist: {path}"
            }

        try:
            os.startfile(str(path))
        except OSError as error:
            return {
                "success": False,
                "provider": self.name,
                "error": str(error)
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "open_path",
            "path": str(path)
        }

    def _open_known_folder(self, task):
        if isinstance(task, dict):
            folder_name = task.get("folder", "")
        else:
            folder_name = str(task)

        folder_name = str(folder_name or "").strip().lower()

        if not folder_name:
            return {
                "success": False,
                "provider": self.name,
                "error": "No known folder was provided."
            }

        path = self.KNOWN_FOLDERS.get(folder_name)

        if path is None:
            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f'Folder "{folder_name}" '
                    "is not in the approved folder list."
                )
            }

        return self._open_path({"path": str(path)})

    def _list_processes(self):
        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
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
                "error": str(error)
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

        for row in csv.reader(io.StringIO(result.stdout)):
            if not row:
                continue
            processes.append(
                {
                    "name": row[0] if len(row) > 0 else "",
                    "pid": row[1] if len(row) > 1 else ""
                }
            )

        return {
            "success": True,
            "provider": self.name,
            "capability": "list_processes",
            "count": len(processes),
            "processes": processes
        }

    def _list_windows(self):
        script = (
            "Get-Process | "
            "Where-Object { $_.MainWindowTitle } | "
            "Select-Object ProcessName,Id,MainWindowTitle | "
            "ConvertTo-Json -Compress"
        )

        try:
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    script
                ],
                capture_output=True,
                text=True,
                timeout=15,
                shell=False
            )
        except (
            OSError,
            subprocess.SubprocessError
        ) as error:
            return {
                "success": False,
                "provider": self.name,
                "error": str(error)
            }

        if result.returncode != 0:
            return {
                "success": False,
                "provider": self.name,
                "error": (
                    result.stderr.strip()
                    or "Unable to inspect visible windows."
                )
            }

        raw = result.stdout.strip()

        if not raw:
            data = []
        else:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as error:
                return {
                    "success": False,
                    "provider": self.name,
                    "error": (
                        "Unable to parse visible window data: "
                        f"{error}"
                    )
                }

        if isinstance(data, dict):
            data = [data]

        windows = []

        for item in data if isinstance(data, list) else []:
            title = str(
                item.get("MainWindowTitle", "") or ""
            ).strip()

            if not title:
                continue

            windows.append(
                {
                    "process": str(
                        item.get("ProcessName", "") or ""
                    ),
                    "pid": str(
                        item.get("Id", "") or ""
                    ),
                    "title": title
                }
            )

        return {
            "success": True,
            "provider": self.name,
            "capability": "list_windows",
            "count": len(windows),
            "windows": windows
        }

    def _is_app_running(self, task):
        if isinstance(task, dict):
            app_name = task.get("app", "")
        else:
            app_name = str(task)

        app_name = self._normalize_app_name(app_name)
        executable = self.APP_ALIASES.get(app_name)

        if executable is None:
            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f'Application "{app_name}" '
                    "is not in the approved app list."
                )
            }

        process_result = self._list_processes()

        if not process_result.get("success"):
            return process_result

        expected_name = Path(executable).name.lower()

        matches = [
            item
            for item in process_result.get("processes", [])
            if str(item.get("name", "")).lower()
            == expected_name
        ]

        return {
            "success": True,
            "provider": self.name,
            "capability": "is_app_running",
            "application": app_name,
            "running": bool(matches),
            "matches": matches
        }


    def _list_app_windows(self, task):
        if isinstance(task, dict):
            app_name = task.get("app", "")
        else:
            app_name = str(task)

        app_name = self._normalize_app_name(app_name)
        executable = self.APP_ALIASES.get(app_name)

        if executable is None:
            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f'Application "{app_name}" '
                    "is not in the approved app list."
                )
            }

        window_result = self._list_windows()

        if not window_result.get("success"):
            return window_result

        expected_process = Path(executable).stem.lower()

        matches = [
            item
            for item in window_result.get("windows", [])
            if str(item.get("process", "")).lower()
            == expected_process
        ]

        return {
            "success": True,
            "provider": self.name,
            "capability": "list_app_windows",
            "application": app_name,
            "count": len(matches),
            "windows": matches
        }

    def _focus_app(self, task):
        if isinstance(task, dict):
            app_name = task.get("app", "")
        else:
            app_name = str(task)

        app_name = self._normalize_app_name(app_name)

        if app_name not in self.APP_ALIASES:
            return {
                "success": False,
                "provider": self.name,
                "error": (
                    f'Application "{app_name}" '
                    "is not in the approved app list."
                )
            }

        window_result = self._list_app_windows(
            {"app": app_name}
        )

        if not window_result.get("success"):
            return window_result

        windows = window_result.get("windows", [])

        if not windows:
            return {
                "success": False,
                "provider": self.name,
                "capability": "focus_app",
                "application": app_name,
                "error": (
                    f'No visible window for "{app_name}" '
                    "is currently available to focus."
                )
            }

        pid = str(windows[0].get("pid", "")).strip()

        if not pid.isdigit():
            return {
                "success": False,
                "provider": self.name,
                "capability": "focus_app",
                "application": app_name,
                "error": "The target window PID was invalid."
            }

        script = (
            "$shell = New-Object -ComObject WScript.Shell; "
            f"$ok = $shell.AppActivate({pid}); "
            "if ($ok) { exit 0 } else { exit 1 }"
        )

        try:
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    script
                ],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False
            )
        except (
            OSError,
            subprocess.SubprocessError
        ) as error:
            return {
                "success": False,
                "provider": self.name,
                "capability": "focus_app",
                "application": app_name,
                "error": str(error)
            }

        if result.returncode != 0:
            return {
                "success": False,
                "provider": self.name,
                "capability": "focus_app",
                "application": app_name,
                "error": (
                    f'Windows could not bring "{app_name}" '
                    "to the foreground."
                )
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "focus_app",
            "application": app_name,
            "pid": pid,
            "title": windows[0].get("title", "")
        }

    def _run_command(self, task):
        """
        Execute a command without shell=True.

        CommandPolicy and PermissionManager remain
        responsible for deciding whether it is permitted.
        """

        if isinstance(task, dict):
            command = task.get("command", "")
            cwd = task.get("cwd")
        else:
            command = str(task)
            cwd = None

        command = str(command or "").strip()

        if not command:
            return {
                "success": False,
                "provider": self.name,
                "error": "No command was provided."
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
                    "Unable to parse command: "
                    f"{error}"
                )
            }

        parts = [
            part.strip("\"'")
            for part in parts
        ]

        if not parts:
            return {
                "success": False,
                "provider": self.name,
                "error": "No executable was found."
            }

        executable = Path(parts[0]).name.lower()

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
            working_directory = Path(cwd).expanduser()

            if not working_directory.exists():
                return {
                    "success": False,
                    "provider": self.name,
                    "error": (
                        "Working directory does not exist: "
                        f"{working_directory}"
                    )
                }

            working_directory = str(working_directory)
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
                "error": str(error)
            }

        return {
            "success": result.returncode == 0,
            "provider": self.name,
            "capability": "run_command",
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
