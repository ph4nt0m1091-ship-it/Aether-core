from tools.file_tool import FileTool


class FileSkill:
    """
    Handles file-related tasks.
    """

    name = "file"

    def __init__(self, memory):

        self.memory = memory
        self.tool = FileTool()

    def handle(self, message):
        """
        FileSkill does not respond to normal conversation.
        """

        return None

    def execute(self, step):

        action = step["action"]
        data = step["data"]

        if action == "create_folder":

            self.tool.create_folder(data["name"])

        elif action == "create_file":

            self.tool.create_file(data["filename"])