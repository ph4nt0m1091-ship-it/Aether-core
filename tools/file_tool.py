import os
import shutil
from pathlib import Path


class FileTool:
    """
    Controlled local file operations.

    Delete rules:
    - files/symlinks may be deleted
    - only empty folders may be deleted
    - recursive delete is disabled
    - protected roots are refused
    """

    def create_folder(self, folder_name):
        try:
            path = Path(folder_name).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(path)}
        except OSError as error:
            return {"success": False, "error": str(error)}

    def create_file(self, filename):
        try:
            path = Path(filename).expanduser()

            if path.exists():
                return {
                    "success": False,
                    "error": f'File "{path}" already exists.'
                }

            parent = path.parent

            if str(parent) not in ("", ".") and not parent.exists():
                return {
                    "success": False,
                    "error": f'Folder "{parent}" does not exist.'
                }

            path.touch(exist_ok=False)
            return {"success": True, "path": str(path)}

        except OSError as error:
            return {"success": False, "error": str(error)}

    def list_files(self, path="."):
        try:
            target = Path(path).expanduser()

            if not target.exists():
                return {
                    "success": False,
                    "error": f'Path does not exist: "{target}"'
                }

            if not target.is_dir():
                return {
                    "success": False,
                    "error": f'Path is not a folder: "{target}"'
                }

            items = []

            for item in sorted(
                target.iterdir(),
                key=lambda value: (
                    not value.is_dir(),
                    value.name.lower()
                )
            ):
                items.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "type": "folder" if item.is_dir() else "file"
                    }
                )

            return {
                "success": True,
                "path": str(target),
                "items": items
            }

        except OSError as error:
            return {"success": False, "error": str(error)}

    def move_path(self, source, destination):
        try:
            source_path = Path(source).expanduser()
            destination_path = Path(destination).expanduser()

            if not source_path.exists():
                return {
                    "success": False,
                    "error": f'Source does not exist: "{source_path}"'
                }

            if destination_path.exists():
                return {
                    "success": False,
                    "error": (
                        f'Destination already exists: "{destination_path}"'
                    )
                }

            parent = destination_path.parent

            if str(parent) not in ("", ".") and not parent.exists():
                return {
                    "success": False,
                    "error": (
                        f'Destination folder does not exist: "{parent}"'
                    )
                }

            moved = shutil.move(
                str(source_path),
                str(destination_path)
            )

            return {
                "success": True,
                "source": str(source_path),
                "destination": str(moved)
            }

        except OSError as error:
            return {"success": False, "error": str(error)}

    def rename_path(self, source, new_name):
        try:
            source_path = Path(source).expanduser()

            if not source_path.exists():
                return {
                    "success": False,
                    "error": f'Path does not exist: "{source_path}"'
                }

            new_name = str(new_name or "").strip()

            if not new_name:
                return {
                    "success": False,
                    "error": "No new name was provided."
                }

            if "/" in new_name or "\\" in new_name:
                return {
                    "success": False,
                    "error": (
                        "The new name must be a name only, "
                        "not another path."
                    )
                }

            destination = source_path.parent / new_name

            if destination.exists():
                return {
                    "success": False,
                    "error": (
                        f'Destination already exists: "{destination}"'
                    )
                }

            source_path.rename(destination)

            return {
                "success": True,
                "source": str(source_path),
                "destination": str(destination)
            }

        except OSError as error:
            return {"success": False, "error": str(error)}

    def delete_safety(self, raw_path):
        try:
            target = Path(raw_path).expanduser()

            if not target.exists() and not target.is_symlink():
                return {
                    "success": False,
                    "safe": False,
                    "error": f'Path does not exist: "{target}"'
                }

            resolved = target.resolve(strict=False)

            for protected_path in self._protected_paths():
                if resolved == protected_path:
                    return {
                        "success": True,
                        "safe": False,
                        "path": str(target),
                        "reason": (
                            "Aether refuses to delete a protected "
                            "system or workspace root."
                        )
                    }

            cwd = Path.cwd().resolve()

            if resolved == cwd or resolved in cwd.parents:
                return {
                    "success": True,
                    "safe": False,
                    "path": str(target),
                    "reason": (
                        "Aether refuses to delete the active workspace "
                        "or one of its parent folders."
                    )
                }

            if target.is_symlink():
                kind = "symlink"

            elif target.is_file():
                kind = "file"

            elif target.is_dir():
                if any(target.iterdir()):
                    return {
                        "success": True,
                        "safe": False,
                        "path": str(target),
                        "kind": "folder",
                        "reason": (
                            "Recursive folder deletion is disabled. "
                            "Only empty folders can be deleted."
                        )
                    }

                kind = "folder"

            else:
                return {
                    "success": True,
                    "safe": False,
                    "path": str(target),
                    "reason": (
                        "This path type is not supported for deletion."
                    )
                }

            return {
                "success": True,
                "safe": True,
                "path": str(target),
                "kind": kind
            }

        except OSError as error:
            return {
                "success": False,
                "safe": False,
                "error": str(error)
            }

    def delete_path(self, raw_path):
        safety = self.delete_safety(raw_path)

        if not safety.get("success"):
            return safety

        if not safety.get("safe"):
            return {
                "success": False,
                "error": safety.get(
                    "reason",
                    "Deletion refused by safety policy."
                )
            }

        target = Path(safety["path"]).expanduser()

        try:
            if target.is_symlink() or target.is_file():
                target.unlink()
            elif target.is_dir():
                target.rmdir()
            else:
                return {
                    "success": False,
                    "error": "Unsupported path type."
                }

            return {
                "success": True,
                "path": str(target),
                "kind": safety.get("kind", "item")
            }

        except OSError as error:
            return {"success": False, "error": str(error)}

    def _protected_paths(self):
        paths = set()

        candidates = [
            Path.home(),
            Path.home().anchor,
            os.environ.get("SystemRoot"),
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
            os.environ.get("ProgramData")
        ]

        system_root = os.environ.get("SystemRoot")

        if system_root:
            candidates.append(Path(system_root) / "System32")

        for candidate in candidates:
            if not candidate:
                continue

            try:
                paths.add(
                    Path(candidate)
                    .expanduser()
                    .resolve(strict=False)
                )
            except OSError:
                continue

        return paths
