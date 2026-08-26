import os
import shutil
from pathlib import Path


class FileTool:
    """
    Handles controlled local file operations.
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
                return {"success": False, "error": f'File "{path}" already exists.'}
            parent = path.parent
            if str(parent) not in ("", ".") and not parent.exists():
                return {"success": False, "error": f'Folder "{parent}" does not exist.'}
            path.touch(exist_ok=False)
            return {"success": True, "path": str(path)}
        except OSError as error:
            return {"success": False, "error": str(error)}

    def list_files(self, path="."):
        try:
            target = Path(path).expanduser()
            if not target.exists():
                return {"success": False, "error": f'Path does not exist: "{target}"'}
            if not target.is_dir():
                return {"success": False, "error": f'Path is not a folder: "{target}"'}
            items = []
            for item in sorted(target.iterdir(), key=lambda value: (not value.is_dir(), value.name.lower())):
                items.append({"name": item.name, "path": str(item), "type": "folder" if item.is_dir() else "file"})
            return {"success": True, "path": str(target), "items": items}
        except OSError as error:
            return {"success": False, "error": str(error)}

    def move_path(self, source, destination):
        try:
            source_path = Path(source).expanduser()
            destination_path = Path(destination).expanduser()
            if not source_path.exists():
                return {"success": False, "error": f'Source does not exist: "{source_path}"'}
            if destination_path.exists():
                return {"success": False, "error": f'Destination already exists: "{destination_path}"'}
            parent = destination_path.parent
            if str(parent) not in ("", ".") and not parent.exists():
                return {"success": False, "error": f'Destination folder does not exist: "{parent}"'}
            moved = shutil.move(str(source_path), str(destination_path))
            return {"success": True, "source": str(source_path), "destination": str(moved)}
        except OSError as error:
            return {"success": False, "error": str(error)}

    def rename_path(self, source, new_name):
        try:
            source_path = Path(source).expanduser()
            if not source_path.exists():
                return {"success": False, "error": f'Path does not exist: "{source_path}"'}
            new_name = str(new_name or "").strip()
            if not new_name:
                return {"success": False, "error": "No new name was provided."}
            if "/" in new_name or "\\" in new_name:
                return {"success": False, "error": "The new name must be a name only, not another path."}
            destination = source_path.parent / new_name
            if destination.exists():
                return {"success": False, "error": f'Destination already exists: "{destination}"'}
            source_path.rename(destination)
            return {"success": True, "source": str(source_path), "destination": str(destination)}
        except OSError as error:
            return {"success": False, "error": str(error)}
