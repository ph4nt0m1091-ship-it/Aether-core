import csv
import ctypes
import time
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

    TEXT_INPUT_APPS = {
        "notepad",
        "vscode",
        "vs code",
        "visual studio code"
    }

    CLOSEABLE_APPS = {
        "notepad",
        "calculator",
        "calc",
        "paint",
        "vscode",
        "vs code",
        "visual studio code"
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
            "minimize_app",
            "maximize_app",
            "restore_app",
            "type_text",
            "close_app",
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
        if capability == "minimize_app":
            return self._set_window_state(task, "minimize")
        if capability == "maximize_app":
            return self._set_window_state(task, "maximize")
        if capability == "restore_app":
            return self._set_window_state(task, "restore")
        if capability == "type_text":
            return self._type_text(task)
        if capability == "close_app":
            return self._close_app(task)
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



    def _set_window_state(self, task, state):
        """Change an approved visible app window state safely."""
        if isinstance(task, dict):
            app_name = task.get("app", "")
        else:
            app_name = str(task)

        app_name = self._normalize_app_name(app_name)

        if app_name not in self.APP_ALIASES:
            return {
                "success": False,
                "provider": self.name,
                "capability": f"{state}_app",
                "error": (
                    f'Application "{app_name}" '
                    "is not in the approved app list."
                )
            }

        show_codes = {
            "minimize": 6,
            "maximize": 3,
            "restore": 9
        }
        show_code = show_codes.get(state)
        if show_code is None:
            return {
                "success": False,
                "provider": self.name,
                "error": f'Unsupported window state: "{state}"'
            }

        window_result = self._list_app_windows({"app": app_name})
        if not window_result.get("success"):
            return window_result

        windows = window_result.get("windows", [])
        if not windows:
            return {
                "success": False,
                "provider": self.name,
                "capability": f"{state}_app",
                "application": app_name,
                "error": (
                    f'No visible window for "{app_name}" '
                    f'is currently available to {state}.'
                )
            }

        pid = str(windows[0].get("pid", "")).strip()
        if not pid.isdigit():
            return {
                "success": False,
                "provider": self.name,
                "capability": f"{state}_app",
                "application": app_name,
                "error": "The target window PID was invalid."
            }

        script = (
            "Add-Type -TypeDefinition '"
            "using System; using System.Runtime.InteropServices; "
            "public static class AetherWin32 { "
            "[DllImport(\"user32.dll\")] "
            "public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow); "
            "}'; "
            f"$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue; "
            "if ($null -eq $p) { exit 2 }; "
            "$h = $p.MainWindowHandle; if ($h -eq 0) { exit 3 }; "
            f"$ok = [AetherWin32]::ShowWindow($h, {show_code}); "
            "if ($ok) { exit 0 } else { exit 1 }"
        )

        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False
            )
        except (OSError, subprocess.SubprocessError) as error:
            return {
                "success": False,
                "provider": self.name,
                "capability": f"{state}_app",
                "application": app_name,
                "error": str(error)
            }

        if result.returncode != 0:
            return {
                "success": False,
                "provider": self.name,
                "capability": f"{state}_app",
                "application": app_name,
                "error": f'Windows could not {state} "{app_name}".'
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": f"{state}_app",
            "application": app_name,
            "pid": pid,
            "title": windows[0].get("title", ""),
            "state": state
        }


    def _type_text(self, task):
        """
        Type literal Unicode text into an approved visible app.

        Safety boundaries:
        - explicit permission_granted=True is required
        - only approved text-input apps are allowed
        - no Enter, Tab, control characters, or hotkeys
        - maximum 500 characters
        - text is emitted as Unicode key events, not shell input
        """

        if not isinstance(task, dict):
            return {
                "success": False,
                "provider": self.name,
                "capability": "type_text",
                "error": "Text input requires a structured task."
            }

        app_name = self._normalize_app_name(
            task.get("app", "")
        )
        text = str(
            task.get("text", "")
        )
        permission_granted = (
            task.get("permission_granted")
            is True
        )

        if app_name not in self.APP_ALIASES:
            return {
                "success": False,
                "provider": self.name,
                "capability": "type_text",
                "error": (
                    f'Application "{app_name}" '
                    "is not in the approved app list."
                )
            }

        if app_name not in self.TEXT_INPUT_APPS:
            return {
                "success": False,
                "provider": self.name,
                "capability": "type_text",
                "application": app_name,
                "error": (
                    f'Application "{app_name}" is not approved '
                    "for text input."
                )
            }

        if not permission_granted:
            return {
                "success": False,
                "provider": self.name,
                "capability": "type_text",
                "application": app_name,
                "requires_permission": True,
                "error": (
                    "Explicit permission is required before "
                    "typing into an application."
                )
            }

        if not text:
            return {
                "success": False,
                "provider": self.name,
                "capability": "type_text",
                "application": app_name,
                "error": "No text was provided."
            }

        if len(text) > 500:
            return {
                "success": False,
                "provider": self.name,
                "capability": "type_text",
                "application": app_name,
                "error": (
                    "Text input is limited to 500 characters "
                    "per action."
                )
            }

        if any(
            ord(character) < 32
            or ord(character) == 127
            for character in text
        ):
            return {
                "success": False,
                "provider": self.name,
                "capability": "type_text",
                "application": app_name,
                "error": (
                    "Control characters, newlines, tabs, and "
                    "submit keys are not allowed."
                )
            }

        focus_result = self._focus_app(
            {
                "app": app_name
            }
        )

        if not focus_result.get(
            "success"
        ):
            return {
                "success": False,
                "provider": self.name,
                "capability": "type_text",
                "application": app_name,
                "error": (
                    "The target app could not be focused safely. "
                    f"{focus_result.get('error', '')}"
                ).strip()
            }

        time.sleep(0.20)

        try:
            user32 = ctypes.windll.user32

            if ctypes.sizeof(ctypes.c_void_p) == 8:
                ULONG_PTR = ctypes.c_ulonglong
            else:
                ULONG_PTR = ctypes.c_ulong

            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [
                    ("dx", ctypes.wintypes.LONG),
                    ("dy", ctypes.wintypes.LONG),
                    ("mouseData", ctypes.wintypes.DWORD),
                    ("dwFlags", ctypes.wintypes.DWORD),
                    ("time", ctypes.wintypes.DWORD),
                    ("dwExtraInfo", ULONG_PTR)
                ]

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", ctypes.wintypes.WORD),
                    ("wScan", ctypes.wintypes.WORD),
                    ("dwFlags", ctypes.wintypes.DWORD),
                    ("time", ctypes.wintypes.DWORD),
                    ("dwExtraInfo", ULONG_PTR)
                ]

            class HARDWAREINPUT(ctypes.Structure):
                _fields_ = [
                    ("uMsg", ctypes.wintypes.DWORD),
                    ("wParamL", ctypes.wintypes.WORD),
                    ("wParamH", ctypes.wintypes.WORD)
                ]

            class INPUT_UNION(ctypes.Union):
                _fields_ = [
                    ("mi", MOUSEINPUT),
                    ("ki", KEYBDINPUT),
                    ("hi", HARDWAREINPUT)
                ]

            class INPUT(ctypes.Structure):
                _anonymous_ = ("union",)
                _fields_ = [
                    ("type", ctypes.wintypes.DWORD),
                    ("union", INPUT_UNION)
                ]

            input_keyboard = 1
            keyeventf_keyup = 0x0002
            keyeventf_unicode = 0x0004

            utf16 = text.encode(
                "utf-16-le"
            )

            for index in range(
                0,
                len(utf16),
                2
            ):
                unit = int.from_bytes(
                    utf16[
                        index:index + 2
                    ],
                    "little"
                )

                events = (
                    INPUT * 2
                )(
                    INPUT(
                        type=input_keyboard,
                        ki=KEYBDINPUT(
                            0,
                            unit,
                            keyeventf_unicode,
                            0,
                            0
                        )
                    ),
                    INPUT(
                        type=input_keyboard,
                        ki=KEYBDINPUT(
                            0,
                            unit,
                            (
                                keyeventf_unicode
                                | keyeventf_keyup
                            ),
                            0,
                            0
                        )
                    )
                )

                sent = user32.SendInput(
                    2,
                    events,
                    ctypes.sizeof(INPUT)
                )

                if sent != 2:
                    return {
                        "success": False,
                        "provider": self.name,
                        "capability": "type_text",
                        "application": app_name,
                        "error": (
                            "Windows did not accept all "
                            "text input events."
                        )
                    }

        except (
            AttributeError,
            OSError,
            ValueError
        ) as error:
            return {
                "success": False,
                "provider": self.name,
                "capability": "type_text",
                "application": app_name,
                "error": str(
                    error
                )
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "type_text",
            "application": app_name,
            "characters": len(
                text
            ),
            "submitted": False
        }

    def _close_app(self, task):
        """
        Gracefully request that an approved application's
        visible windows close.

        This capability never force-kills a process.
        The caller must explicitly provide permission_granted=True.
        """

        if isinstance(task, dict):
            app_name = task.get("app", "")
            permission_granted = (
                task.get("permission_granted")
                is True
            )
        else:
            app_name = str(task)
            permission_granted = False

        app_name = self._normalize_app_name(app_name)

        if app_name not in self.APP_ALIASES:
            return {
                "success": False,
                "provider": self.name,
                "capability": "close_app",
                "error": (
                    f'Application "{app_name}" '
                    "is not in the approved app list."
                )
            }

        if app_name not in self.CLOSEABLE_APPS:
            return {
                "success": False,
                "provider": self.name,
                "capability": "close_app",
                "application": app_name,
                "error": (
                    f'Application "{app_name}" is not approved '
                    "for graceful closing."
                )
            }

        if not permission_granted:
            return {
                "success": False,
                "provider": self.name,
                "capability": "close_app",
                "application": app_name,
                "requires_permission": True,
                "error": (
                    "Explicit permission is required before "
                    "closing an application."
                )
            }

        window_result = self._list_app_windows(
            {
                "app": app_name
            }
        )

        if not window_result.get("success"):
            return window_result

        windows = window_result.get(
            "windows",
            []
        )

        if not windows:
            return {
                "success": False,
                "provider": self.name,
                "capability": "close_app",
                "application": app_name,
                "error": (
                    f'No visible window for "{app_name}" '
                    "is currently available to close."
                )
            }

        pids = []

        for window in windows:
            pid = str(
                window.get(
                    "pid",
                    ""
                )
            ).strip()

            if (
                pid.isdigit()
                and pid not in pids
            ):
                pids.append(
                    pid
                )

        if not pids:
            return {
                "success": False,
                "provider": self.name,
                "capability": "close_app",
                "application": app_name,
                "error": (
                    "No valid visible-window process IDs "
                    "were available."
                )
            }

        closed = []
        refused = []

        for pid in pids:
            script = (
                f"$p = Get-Process -Id {pid} "
                "-ErrorAction SilentlyContinue; "
                "if ($null -eq $p) { exit 2 }; "
                "$ok = $p.CloseMainWindow(); "
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
                    "capability": "close_app",
                    "application": app_name,
                    "error": str(
                        error
                    )
                }

            if result.returncode == 0:
                closed.append(
                    pid
                )
            else:
                refused.append(
                    pid
                )

        if not closed:
            return {
                "success": False,
                "provider": self.name,
                "capability": "close_app",
                "application": app_name,
                "error": (
                    "Windows did not accept a graceful close "
                    "request for the visible application window."
                ),
                "refused_pids": refused
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "close_app",
            "application": app_name,
            "closed_pids": closed,
            "refused_pids": refused,
            "forced": False
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
