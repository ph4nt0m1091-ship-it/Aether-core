import os


class FileTool:

    def create_folder(self, folder_name):

        try:

            os.makedirs(folder_name, exist_ok=True)
            return True

        except Exception:

            return False

    def create_file(self, filename):

        try:

            with open(filename, "w") as file:
                file.write("")

            return True

        except Exception:

            return False

    def list_files(self, path="."):

        try:

            return os.listdir(path)

        except Exception:

            return None