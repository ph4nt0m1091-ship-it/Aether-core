from pathlib import Path

from permissions.permission_manager import PermissionManager
from tools.file_tool import FileTool


class FileSkill:
    """
    Handles file-related tasks.

    Supports:
    - Natural folder listing
    - Natural folder creation
    - Explicit file creation
    - Permission-gated move and rename
    - Permission-gated conservative delete
    - Create-only workflow text output

    Delete is deliberately strict:
    - explicit path/name required
    - always requires approval
    - recursive folder deletion is disabled
    - protected roots are refused
    """

    name = "file"

    description = (
        "Creates, lists, moves, renames, and safely "
        "deletes local files and folders."
    )

    def __init__(self, memory):
        self.memory = memory
        self.tool = FileTool()
        self.permissions = PermissionManager()

    def handle(self, message):
        message = str(message or "").strip()

        if not message:
            return None

        if self.permissions.has_pending():
            response = (
                self.permissions
                .interpret_response(
                    message
                )
            )

            if response == "approve":
                pending = (
                    self.permissions
                    .consume()
                )

                action = pending.get(
                    "action",
                    ""
                )

                data = pending.get(
                    "data",
                    {}
                )

                if action == "move_path":
                    return self._move_path(
                        data.get("source", ""),
                        data.get("destination", "")
                    )

                if action == "rename_path":
                    return self._rename_path(
                        data.get("source", ""),
                        data.get("new_name", "")
                    )

                if action == "delete_path":
                    return self._delete_path(
                        data.get("path", "")
                    )

                return (
                    "Aether: File action could not "
                    "be resumed safely."
                )

            if response == "deny":
                self.permissions.cancel()
                return "Aether: File action cancelled."

            return (
                "Aether: I am waiting for permission.\n"
                'Say "yes" to approve or "no" to cancel.'
            )

        lower = (
            message.lower()
            .rstrip("?")
        )

        current_folder_requests = (
            "show files",
            "list files",
            "show files here",
            "list files here",
            "show files in this folder",
            "list files in this folder",
            "show this folder",
            "list this folder"
        )

        if lower in current_folder_requests:
            return self._list_folder(".")

        list_prefixes = (
            "show files in ",
            "list files in ",
            "show contents of ",
            "list contents of "
        )

        for prefix in list_prefixes:
            if lower.startswith(prefix):
                raw_path = (
                    message[
                        len(prefix):
                    ]
                    .strip()
                )

                if not raw_path:
                    return (
                        "Aether: Which folder "
                        "should I inspect?"
                    )

                return self._list_folder(
                    self._expand_common_path(
                        raw_path
                    )
                )

        create_folder_prefixes = (
            "create a folder called ",
            "create folder called ",
            "make a folder called ",
            "make folder called ",
            "create folder ",
            "make folder "
        )

        for prefix in create_folder_prefixes:
            if lower.startswith(prefix):
                raw_name = (
                    message[
                        len(prefix):
                    ]
                    .strip()
                )

                if not raw_name:
                    return (
                        "Aether: What should "
                        "the folder be called?"
                    )

                return self._create_folder(
                    self._parse_folder_target(
                        raw_name
                    )
                )

        create_file_prefixes = (
            "create a file called ",
            "create file called ",
            "make a file called ",
            "make file called ",
            "create file ",
            "make file "
        )

        for prefix in create_file_prefixes:
            if lower.startswith(prefix):
                filename = (
                    message[
                        len(prefix):
                    ]
                    .strip()
                )

                if not filename:
                    return (
                        "Aether: What should "
                        "the file be called?"
                    )

                return self._create_file(
                    self._expand_common_path(
                        filename
                    )
                )

        delete_prefixes = (
            "delete file ",
            "delete folder ",
            "delete ",
            "remove file ",
            "remove folder "
        )

        for prefix in delete_prefixes:
            if lower.startswith(prefix):
                raw_path = (
                    message[
                        len(prefix):
                    ]
                    .strip()
                )

                if not raw_path:
                    return (
                        "Aether: Which exact file "
                        "or folder should I delete?"
                    )

                target = self._expand_common_path(
                    raw_path
                )

                safety = self.tool.delete_safety(
                    target
                )

                if not safety.get("success"):
                    return (
                        "Aether: I couldn't inspect "
                        "that delete request.\n"
                        f"{safety.get('error', '')}"
                    ).rstrip()

                if not safety.get("safe"):
                    return (
                        "Aether: Delete blocked.\n"
                        f"Reason: {safety.get('reason', '')}\n\n"
                        "Nothing was deleted."
                    ).rstrip()

                self.permissions.request(
                    "delete_path",
                    {
                        "path": target
                    }
                )

                kind = safety.get(
                    "kind",
                    "item"
                )

                return (
                    "Aether: Permission required.\n\n"
                    f"Delete {kind}: {target}\n\n"
                    "This permanently removes the selected item. "
                    "Recursive folder deletion is disabled.\n\n"
                    'Say "yes" to approve or "no" to cancel.'
                )

        if lower.startswith("move "):
            body = (
                message[
                    len("move "):
                ]
                .strip()
            )

            separator = " to "

            if separator in body.lower():
                index = body.lower().find(
                    separator
                )

                source = body[:index].strip()
                destination = (
                    body[
                        index
                        + len(separator):
                    ]
                    .strip()
                )

                if source and destination:
                    source = self._expand_common_path(
                        source
                    )

                    destination = self._expand_common_path(
                        destination
                    )

                    self.permissions.request(
                        "move_path",
                        {
                            "source": source,
                            "destination": destination
                        }
                    )

                    return (
                        "Aether: Permission required.\n\n"
                        f"Move: {source}\n"
                        f"To: {destination}\n\n"
                        "Moving a file or folder changes "
                        "its location.\n\n"
                        'Say "yes" to approve or "no" to cancel.'
                    )

        if lower.startswith("rename "):
            body = (
                message[
                    len("rename "):
                ]
                .strip()
            )

            separator = " to "

            if separator in body.lower():
                index = body.lower().find(
                    separator
                )

                source = body[:index].strip()
                new_name = (
                    body[
                        index
                        + len(separator):
                    ]
                    .strip()
                )

                if source and new_name:
                    source = self._expand_common_path(
                        source
                    )

                    self.permissions.request(
                        "rename_path",
                        {
                            "source": source,
                            "new_name": new_name
                        }
                    )

                    return (
                        "Aether: Permission required.\n\n"
                        f"Rename: {source}\n"
                        f"New name: {new_name}\n\n"
                        "Renaming changes an existing "
                        "file or folder.\n\n"
                        'Say "yes" to approve or "no" to cancel.'
                    )

        return None

    def _expand_common_path(self, raw_path):
        raw_path = (
            str(
                raw_path or ""
            )
            .strip()
            .strip('"')
        )

        lower = (
            raw_path.lower()
            .rstrip("\\/")
        )

        home = Path.home()

        aliases = {
            "home": home,
            "my home": home,
            "documents": home / "Documents",
            "my documents": home / "Documents",
            "downloads": home / "Downloads",
            "my downloads": home / "Downloads",
            "desktop": home / "Desktop",
            "my desktop": home / "Desktop",
            "this folder": Path("."),
            "current folder": Path(".")
        }

        if lower in aliases:
            return str(
                aliases[
                    lower
                ]
            )

        return raw_path

    def _parse_folder_target(self, raw_name):
        raw_name = str(
            raw_name or ""
        ).strip()

        lower = raw_name.lower()
        marker = " in "

        if marker in lower:
            index = lower.rfind(
                marker
            )

            folder_name = raw_name[:index].strip()

            parent_name = (
                raw_name[
                    index
                    + len(marker):
                ]
                .strip()
            )

            parent = Path(
                self._expand_common_path(
                    parent_name
                )
            )

            return str(
                parent
                / folder_name
            )

        return self._expand_common_path(
            raw_name
        )

    def _list_folder(self, path):
        result = self.tool.list_files(
            path
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't list that folder.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        items = result.get(
            "items",
            []
        )

        if not items:
            return (
                "Aether: That folder is empty.\n"
                f"Folder: {result.get('path')}"
            )

        output = (
            "Aether: Folder Contents\n\n"
            f"Folder: {result.get('path')}\n\n"
        )

        max_items = 50

        for item in items[:max_items]:
            marker = (
                "[Folder]"
                if item.get("type") == "folder"
                else "[File]"
            )

            output += (
                f"{marker} "
                f"{item.get('name')}\n"
            )

        if len(items) > max_items:
            output += (
                "\nShowing the first "
                f"{max_items} of "
                f"{len(items)} items."
            )

        return output.rstrip()

    def _create_folder(self, name):
        result = self.tool.create_folder(
            name
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't create that folder.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        return (
            "Aether: Folder created.\n\n"
            f"{result.get('path')}"
        )

    def _create_file(self, filename):
        result = self.tool.create_file(
            filename
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't create that file.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        return (
            "Aether: File created.\n\n"
            f"{result.get('path')}"
        )

    def _move_path(self, source, destination):
        result = self.tool.move_path(
            source,
            destination
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't move that file or folder.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        return (
            "Aether: Move completed.\n\n"
            f"From: {result.get('source')}\n"
            f"To: {result.get('destination')}"
        )

    def _rename_path(self, source, new_name):
        result = self.tool.rename_path(
            source,
            new_name
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't rename that file or folder.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        return (
            "Aether: Rename completed.\n\n"
            f"From: {result.get('source')}\n"
            f"To: {result.get('destination')}"
        )

    def _delete_path(self, path):
        result = self.tool.delete_path(
            path
        )

        if not result.get("success"):
            return (
                "Aether: I couldn't delete that item.\n"
                f"{result.get('error', '')}\n\n"
                "Nothing was deleted."
            ).rstrip()

        return (
            "Aether: Delete completed.\n\n"
            f"Deleted {result.get('kind', 'item')}: "
            f"{result.get('path')}"
        )

    def execute(self, step):
        action = step.get(
            "action",
            ""
        )

        data = step.get(
            "data",
            {}
        )

        if action == "create_folder":
            name = data.get(
                "name"
            )

            if not name:
                return {
                    "success": False,
                    "error": "No folder name was provided."
                }

            result = self.tool.create_folder(
                name
            )

            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get(
                        "error",
                        "Folder creation failed."
                    )
                }

            return {
                "success": True,
                "action": action,
                "response": (
                    f"Folder created: {result.get('path')}"
                )
            }

        if action == "create_file":
            filename = data.get(
                "filename"
            )

            if not filename:
                return {
                    "success": False,
                    "error": "No filename was provided."
                }

            result = self.tool.create_file(
                filename
            )

            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get(
                        "error",
                        "File creation failed."
                    )
                }

            return {
                "success": True,
                "action": action,
                "response": (
                    f"File created: {result.get('path')}"
                )
            }

        if action == "write_text":
            filename = str(
                data.get(
                    "filename",
                    ""
                )
            ).strip()

            content = data.get(
                "content",
                ""
            )

            if not filename:
                return {
                    "success": False,
                    "error": "No output filename was provided."
                }

            path = Path(
                filename
            )

            if path.exists():
                return {
                    "success": False,
                    "error": (
                        f'File "{filename}" already exists. '
                        "Aether refused to overwrite it."
                    )
                }

            parent = path.parent

            if (
                str(parent) not in ("", ".")
                and not parent.exists()
            ):
                return {
                    "success": False,
                    "error": f'Folder "{parent}" does not exist.'
                }

            try:
                path.write_text(
                    str(content),
                    encoding="utf-8"
                )
            except OSError as error:
                return {
                    "success": False,
                    "error": str(error)
                }

            return {
                "success": True,
                "action": action,
                "filename": str(path),
                "output": str(content),
                "response": (
                    "Workflow output saved to "
                    f"{path}"
                )
            }

        return {
            "success": False,
            "error": f'Unknown file action: "{action}"'
        }
