class DesktopSkill:
    """
    Safe natural-language desktop inspection and launching.

    DesktopSkill intentionally stays low risk:
    - inspect visible application windows
    - check whether an approved app is running
    - inspect visible windows for an approved app
    - focus an approved running app
    - open approved user folders

    It does not click, type, close processes, delete files,
    or execute arbitrary commands.
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
