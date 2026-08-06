from tools.file_tool import FileTool


class FileSkill:

    def __init__(self):

        self.tool = FileTool()

    def execute(self, step):

        action = step["action"]
        data = step["data"]

        if action == "create_folder":

            self.tool.create_folder(data["name"])

        elif action == "create_file":

            self.tool.create_file(data["filename"])