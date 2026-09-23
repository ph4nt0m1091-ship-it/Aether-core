import time

from permissions.permission_manager import PermissionManager


class DesktopSkill:
    """
    Safe natural-language desktop inspection and launching.

    DesktopSkill intentionally stays low risk:
    - inspect visible application windows
    - check whether an approved app is running
    - inspect visible windows for an approved app
    - focus an approved running app
    - open approved user folders

    It does not click arbitrary coordinates, send hotkeys,
    force-kill processes, delete files, or execute arbitrary commands.
    Text input is explicit, permission-gated, and never auto-submits.
    """

    name = "desktop"

    description = (
        "Provides safe desktop inspection and approved "
        "Windows folder opening."
    )

    def __init__(self, memory):
        self.memory = memory
        self.skill_manager = None
        self.last_execution_result = None
        self.permissions = PermissionManager()

    def connect(self, skill_manager):
        self.skill_manager = skill_manager

    def _provider(self):
        if self.skill_manager is None:
            return None

        return (
            self.skill_manager
            .registry
            .provider_skill
            .manager
            .get("local_system")
        )

    def _execute(self, capability, task):
        if self.skill_manager is None:
            return {
                "success": False,
                "error": "Skill manager is unavailable."
            }

        provider_skill = (
            self.skill_manager
            .registry
            .provider_skill
        )

        result = (
            provider_skill.manager.execute(
                capability,
                task,
                provider_name="local_system"
            )
        )

        self.last_execution_result = result
        return result


    def _approved_app(self, app_name):
        provider = self._provider()

        if provider is None:
            return None

        normalized = provider._normalize_app_name(
            app_name
        )

        if normalized not in provider.APP_ALIASES:
            return None

        return normalized

    def handle(self, message):
        text = str(message or "").strip()
        lower = text.lower()

        if not lower:
            return None

        if self.permissions.has_pending():
            response = (
                self.permissions
                .interpret_response(
                    text
                )
            )

            if response == "approve":
                pending = (
                    self.permissions
                    .consume()
                )

                action = pending.get(
                    "action"
                )
                data = pending.get(
                    "data",
                    {}
                )

                if action == "close_app":
                    return (
                        self._close_app_approved(
                            data.get(
                                "app",
                                ""
                            )
                        )
                    )

                if action == "type_text":
                    return (
                        self._type_text_approved(
                            data.get(
                                "app",
                                ""
                            ),
                            data.get(
                                "text",
                                ""
                            )
                        )
                    )

                if action == "press_key":
                    return (
                        self._press_key_approved(
                            data.get(
                                "app",
                                ""
                            ),
                            data.get(
                                "key",
                                ""
                            )
                        )
                    )

                return (
                    "Aether: Desktop action could not "
                    "be resumed safely."
                )

            if response == "deny":
                pending = (
                    self.permissions
                    .cancel()
                )

                return (
                    "Aether: Desktop action cancelled."
                )

            return (
                "Aether: I am waiting for permission.\n"
                'Say "yes" to approve or "no" to cancel.'
            )

        if lower in (
            "show my open windows",
            "show open windows",
            "list open windows",
            "what windows are open",
            "what apps are open",
            "show visible windows"
        ):
            return self._show_windows()

        running_prefixes = (
            "is ",
            "check if "
        )

        running_suffixes = (
            " running",
            " open"
        )

        for prefix in running_prefixes:
            if not lower.startswith(prefix):
                continue

            body = text[len(prefix):].strip()
            body_lower = body.lower()

            for suffix in running_suffixes:
                if not body_lower.endswith(suffix):
                    continue

                app_name = body[
                    :len(body) - len(suffix)
                ].strip()

                if not app_name:
                    return None

                approved = self._approved_app(
                    app_name
                )

                if approved is None:
                    return None

                return self._show_app_running(
                    approved
                )


        window_prefixes = (
            "show windows for ",
            "list windows for ",
            "show open windows for ",
            "what windows does "
        )

        for prefix in window_prefixes:
            if not lower.startswith(prefix):
                continue

            app_name = text[len(prefix):].strip()

            if prefix == "what windows does ":
                suffix = " have open"
                if app_name.lower().endswith(suffix):
                    app_name = app_name[:-len(suffix)].strip()

            approved = self._approved_app(
                app_name
            )

            if approved is None:
                return None

            return self._show_app_windows(
                approved
            )

        focus_prefixes = (
            "focus ",
            "focus on ",
            "bring up ",
            "bring forward ",
            "bring to front ",
            "switch to "
        )

        for prefix in focus_prefixes:
            if not lower.startswith(prefix):
                continue

            app_name = text[len(prefix):].strip()

            approved = self._approved_app(
                app_name
            )

            if approved is None:
                return None

            return self._focus_app(
                approved
            )





        key_prefixes = (
            "press ",
            "hit "
        )

        for prefix in key_prefixes:
            if not lower.startswith(
                prefix
            ):
                continue

            body = text[
                len(prefix):
            ].strip()

            left, found, right = (
                body.rpartition(
                    " in "
                )
            )

            if not found:
                continue

            key_name = left.strip().lower()
            app_name = right.strip()

            approved = self._approved_app(
                app_name
            )

            if approved is None:
                return None

            provider = self._provider()

            if (
                provider is None
                or approved not in provider.TEXT_INPUT_APPS
            ):
                return (
                    "Aether: That application is not approved "
                    "for key input."
                )

            if key_name not in provider.KEY_ALIASES:
                return (
                    "Aether: That key is not approved. "
                    "Allowed keys are Enter, Escape, and Tab."
                )

            preview_result = (
                self._execute(
                    "list_app_windows",
                    {
                        "app": approved
                    }
                )
            )

            if not preview_result.get(
                "success"
            ):
                return (
                    "Aether: I couldn't inspect "
                    f'"{approved}" before sending the key.\n'
                    f"{preview_result.get('error', '')}"
                ).rstrip()

            if not preview_result.get(
                "windows",
                []
            ):
                return (
                    "Aether: "
                    f"{approved} has no visible window "
                    "available for key input."
                )

            self.permissions.request(
                "press_key",
                {
                    "app": approved,
                    "key": key_name
                }
            )

            return (
                "Aether: Permission required.\n\n"
                f"Send key: {key_name}\n"
                f"Target app: {approved}\n\n"
                "Aether will send one approved key only. "
                "No modifier keys or hotkeys will be sent.\n\n"
                'Say "yes" to approve or "no" to cancel.'
            )

        type_prefixes = (
            "type ",
            "write "
        )

        for prefix in type_prefixes:
            if not lower.startswith(
                prefix
            ):
                continue

            body = text[
                len(prefix):
            ].strip()

            split_markers = (
                " into ",
                " in "
            )

            content = None
            app_name = None

            for marker in split_markers:
                left, found, right = (
                    body.rpartition(
                        marker
                    )
                )

                if (
                    found
                    and left.strip()
                    and right.strip()
                ):
                    content = left.strip()
                    app_name = right.strip()
                    break

            if (
                content is None
                or app_name is None
            ):
                continue

            if (
                len(content) >= 2
                and content[0] == content[-1]
                and content[0] in (
                    '"',
                    "'"
                )
            ):
                content = content[1:-1]

            approved = self._approved_app(
                app_name
            )

            if approved is None:
                return None

            provider = self._provider()

            if (
                provider is None
                or approved not in provider.TEXT_INPUT_APPS
            ):
                return (
                    "Aether: That application is not approved "
                    "for text input."
                )

            if not content:
                return (
                    "Aether: No text was provided."
                )

            if len(content) > 500:
                return (
                    "Aether: Text input is limited to "
                    "500 characters per action."
                )

            if any(
                ord(character) < 32
                or ord(character) == 127
                for character in content
            ):
                return (
                    "Aether: Control characters, newlines, "
                    "tabs, and submit keys are not allowed."
                )

            preview_result = (
                self._execute(
                    "list_app_windows",
                    {
                        "app": approved
                    }
                )
            )

            if not preview_result.get(
                "success"
            ):
                return (
                    "Aether: I couldn't inspect "
                    f'"{approved}" before typing.\n'
                    f"{preview_result.get('error', '')}"
                ).rstrip()

            if not preview_result.get(
                "windows",
                []
            ):
                return (
                    "Aether: "
                    f"{approved} has no visible window "
                    "available for text input."
                )

            self.permissions.request(
                "type_text",
                {
                    "app": approved,
                    "text": content
                }
            )

            preview = content

            if len(preview) > 120:
                preview = (
                    preview[:117]
                    + "..."
                )

            return (
                "Aether: Permission required.\n\n"
                f"Type into: {approved}\n"
                f"Characters: {len(content)}\n"
                f"Preview: {preview}\n\n"
                "Aether will type literal text only. "
                "It will not press Enter, submit, or send "
                "hotkeys.\n\n"
                'Say "yes" to approve or "no" to cancel.'
            )

        window_state_prefixes = {
            "minimize ": "minimize_app",
            "maximize ": "maximize_app",
            "restore window ": "restore_app",
            "restore ": "restore_app"
        }

        for prefix, capability in window_state_prefixes.items():
            if not lower.startswith(prefix):
                continue

            app_name = text[len(prefix):].strip().rstrip("?")
            approved = self._approved_app(app_name)
            if approved is None:
                return None

            return self._change_window_state(
                approved,
                capability
            )

        close_prefixes = (
            "close ",
            "quit ",
            "exit app "
        )

        for prefix in close_prefixes:
            if not lower.startswith(
                prefix
            ):
                continue

            app_name = (
                text[
                    len(prefix):
                ]
                .strip()
                .rstrip("?")
            )

            approved = self._approved_app(
                app_name
            )

            if approved is None:
                return None

            provider = self._provider()

            if (
                provider is None
                or approved not in provider.CLOSEABLE_APPS
            ):
                return (
                    "Aether: That application is not approved "
                    "for graceful closing."
                )

            preview = None
            windows = []

            for attempt in range(4):
                preview = (
                    self._execute(
                        "list_app_windows",
                        {
                            "app": approved
                        }
                    )
                )

                if not preview.get(
                    "success"
                ):
                    return (
                        "Aether: I couldn't inspect "
                        f'"{approved}" before closing it.\n'
                        f"{preview.get('error', '')}"
                    ).rstrip()

                windows = preview.get(
                    "windows",
                    []
                )

                if windows:
                    break

                if attempt < 3:
                    time.sleep(0.35)

            if not windows:
                return (
                    "Aether: "
                    f"{approved} has no visible window to close."
                )

            self.permissions.request(
                "close_app",
                {
                    "app": approved
                }
            )

            output = (
                "Aether: Permission required.\n\n"
                f"Close application: {approved}\n"
                f"Visible windows: {len(windows)}\n\n"
                "Aether will request a normal graceful close. "
                "It will not force-kill the process.\n\n"
                'Say "yes" to approve or "no" to cancel.'
            )

            return output

        folder_phrases = {
            "open desktop": "desktop",
            "open my desktop": "desktop",
            "open documents": "documents",
            "open my documents": "documents",
            "open downloads": "downloads",
            "open my downloads": "downloads",
            "open pictures": "pictures",
            "open my pictures": "pictures",
            "open music": "music",
            "open my music": "music",
            "open videos": "videos",
            "open my videos": "videos",
            "open home folder": "home",
            "open my home folder": "home",
            "open user folder": "user folder",
            "open my user folder": "user folder"
        }

        folder_name = folder_phrases.get(lower)

        if folder_name:
            return self._open_known_folder(
                folder_name
            )

        return None

    def _show_windows(self):
        result = self._execute(
            "list_windows",
            {}
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't inspect "
                "the open windows.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        windows = result.get(
            "windows",
            []
        )

        if not windows:
            return (
                "Aether: I didn't find any "
                "visible application windows."
            )

        display_limit = 30

        output = (
            "Aether: Open Windows\n\n"
        )

        for item in windows[:display_limit]:
            output += (
                f"- {item.get('title', '')}\n"
                f"  Process: "
                f"{item.get('process', '')} "
                f"(PID {item.get('pid', '')})\n"
            )

        total = result.get(
            "count",
            len(windows)
        )

        if total > display_limit:
            output += (
                "\nShowing first "
                f"{display_limit} of {total} windows."
            )

        return output.rstrip()

    def _show_app_running(self, app_name):
        result = self._execute(
            "is_app_running",
            {
                "app": app_name
            }
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't check "
                f'"{app_name}".\n'
                f"{result.get('error', '')}"
            ).rstrip()

        if result.get("running"):
            matches = result.get(
                "matches",
                []
            )

            pids = [
                str(item.get("pid", ""))
                for item in matches
                if item.get("pid")
            ]

            suffix = ""

            if pids:
                suffix = (
                    "\nPID"
                    + (
                        "s"
                        if len(pids) > 1
                        else ""
                    )
                    + ": "
                    + ", ".join(pids)
                )

            return (
                "Aether: Yes — "
                f"{app_name} is running."
                + suffix
            )

        return (
            "Aether: No — "
            f"{app_name} is not running."
        )


    def _show_app_windows(self, app_name):
        result = self._execute(
            "list_app_windows",
            {
                "app": app_name
            }
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't inspect windows for "
                f'"{app_name}".\n'
                f"{result.get('error', '')}"
            ).rstrip()

        windows = result.get(
            "windows",
            []
        )

        if not windows:
            return (
                "Aether: "
                f"{app_name} has no visible windows."
            )

        output = (
            "Aether: Windows for "
            f"{app_name}\n\n"
        )

        for item in windows[:20]:
            output += (
                f"- {item.get('title', '')} "
                f"(PID {item.get('pid', '')})\n"
            )

        return output.rstrip()

    def _focus_app(self, app_name):
        result = self._execute(
            "focus_app",
            {
                "app": app_name
            }
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't focus "
                f'"{app_name}".\n'
                f"{result.get('error', '')}"
            ).rstrip()

        title = str(
            result.get("title", "") or ""
        ).strip()

        if title:
            return (
                "Aether: Brought "
                f"{app_name} to the foreground.\n"
                f"Window: {title}"
            )

        return (
            "Aether: Brought "
            f"{app_name} to the foreground."
        )





    def _press_key_approved(
        self,
        app_name,
        key_name
    ):
        result = self._execute(
            "press_key",
            {
                "app": app_name,
                "key": key_name,
                "permission_granted": True
            }
        )

        if not result.get(
            "success"
        ):
            return (
                "Aether: I couldn't send "
                f'"{key_name}" to "{app_name}".\n'
                f"{result.get('error', '')}"
            ).rstrip()

        return (
            "Aether: Sent "
            f"{key_name} to {app_name}."
        )

    def _type_text_approved(
        self,
        app_name,
        text
    ):
        result = self._execute(
            "type_text",
            {
                "app": app_name,
                "text": text,
                "permission_granted": True
            }
        )

        if not result.get(
            "success"
        ):
            return (
                "Aether: I couldn't type into "
                f'"{app_name}".\n'
                f"{result.get('error', '')}"
            ).rstrip()

        return (
            "Aether: Typed "
            f"{result.get('characters', len(text))} "
            f"characters into {app_name}.\n"
            "No submit key was sent."
        )

    def _change_window_state(self, app_name, capability):
        result = self._execute(
            capability,
            {"app": app_name}
        )

        action_names = {
            "minimize_app": "minimize",
            "maximize_app": "maximize",
            "restore_app": "restore"
        }
        action = action_names.get(capability, "change")

        if not result.get("success"):
            return (
                "Aether: I couldn't "
                f'{action} "{app_name}".\n'
                f"{result.get('error', '')}"
            ).rstrip()

        phrase = {
            "minimize": "Minimized",
            "maximize": "Maximized",
            "restore": "Restored"
        }.get(action, "Updated")

        title = str(result.get("title", "") or "").strip()
        if title:
            return (
                f"Aether: {phrase} {app_name}.\n"
                f"Window: {title}"
            )

        return f"Aether: {phrase} {app_name}."

    def _close_app_approved(
        self,
        app_name
    ):

        result = (
            self._execute(
                "close_app",
                {
                    "app": app_name,
                    "permission_granted": True
                }
            )
        )

        if not result.get(
            "success"
        ):
            return (
                "Aether: I couldn't gracefully close "
                f'"{app_name}".\n'
                f"{result.get('error', '')}"
            ).rstrip()

        closed = result.get(
            "closed_pids",
            []
        )

        return (
            "Aether: Graceful close requested for "
            f"{app_name}.\n"
            f"Window process"
            + (
                "es"
                if len(closed) != 1
                else ""
            )
            + ": "
            + ", ".join(
                str(pid)
                for pid in closed
            )
        )

    def _open_known_folder(self, folder_name):
        result = self._execute(
            "open_known_folder",
            {
                "folder": folder_name
            }
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't open "
                f"{folder_name}.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        return (
            "Aether: Opened "
            f"{folder_name}."
        )

    def execute(self, step):
        return None
