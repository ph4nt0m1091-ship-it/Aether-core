from pathlib import Path

from tools.file_tool import FileTool


class FileSkill:
    """
    Handles file-related tasks.

    Workflow text writes are intentionally
    create-only by default so Aether does not
    silently overwrite an existing file.
    """

    name = "file"

    description = (
        "Creates files and folders and safely "
        "writes workflow output to files."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.tool = FileTool()

    def handle(
        self,
        message
    ):
        """
        FileSkill does not currently respond
        directly to normal conversation.
        """

        return None

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        action = step.get(
            "action",
            ""
        )

        data = step.get(
            "data",
            {}
        )

        # ---------------------------------
        # CREATE FOLDER
        # ---------------------------------

        if action == "create_folder":

            name = data.get(
                "name"
            )

            if not name:

                return {
                    "success": False,
                    "error": (
                        "No folder name was provided."
                    )
                }

            self.tool.create_folder(
                name
            )

            return {
                "success": True,
                "action": action,
                "response": (
                    f"Folder created: {name}"
                )
            }

        # ---------------------------------
        # CREATE FILE
        # ---------------------------------

        if action == "create_file":

            filename = data.get(
                "filename"
            )

            if not filename:

                return {
                    "success": False,
                    "error": (
                        "No filename was provided."
                    )
                }

            self.tool.create_file(
                filename
            )

            return {
                "success": True,
                "action": action,
                "response": (
                    f"File created: {filename}"
                )
            }

        # ---------------------------------
        # WRITE TEXT
        # ---------------------------------

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
                    "error": (
                        "No output filename was provided."
                    )
                }

            path = Path(
                filename
            )

            # Important safety rule:
            # do not silently destroy existing data.
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
                str(parent) not in (
                    "",
                    "."
                )
                and not parent.exists()
            ):

                return {
                    "success": False,
                    "error": (
                        f'Folder "{parent}" does not exist.'
                    )
                }

            try:

                path.write_text(
                    str(content),
                    encoding="utf-8"
                )

            except OSError as error:

                return {
                    "success": False,
                    "error": str(
                        error
                    )
                }

            return {
                "success": True,
                "action": action,
                "filename": str(
                    path
                ),
                "output": str(
                    content
                ),
                "response": (
                    "Workflow output saved to "
                    f"{path}"
                )
            }

        return {
            "success": False,
            "error": (
                f'Unknown file action: "{action}"'
            )
        }