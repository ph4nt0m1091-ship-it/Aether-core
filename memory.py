import json
import os


class Memory:

    def __init__(self):

        self.filename = "data/memory.json"

        self.data = {
            "name": None,
            "favorite_color": None,
            "dog_name": None,
            "likes": []
        }

        self.load()

    # -------------------------
    # LOAD
    # -------------------------

    def load(self):

        if os.path.exists(self.filename):

            with open(self.filename, "r") as file:
                self.data = json.load(file)

    # -------------------------
    # SAVE
    # -------------------------

    def save(self):

        with open(self.filename, "w") as file:
            json.dump(self.data, file, indent=4)

    # -------------------------
    # REMEMBER
    # -------------------------

    def remember(self, text):

        message = text.lower().strip()

        if message.startswith("my name is"):

            self.data["name"] = text[10:].strip(" .")

        elif message.startswith("my favorite color is"):

            self.data["favorite_color"] = text[20:].strip(" .")

        elif message.startswith("my dog's name is"):

            self.data["dog_name"] = text[16:].strip(" .")

        elif message.startswith("i like"):

            like = text[6:].strip(" .")

            if like and like.lower() not in [
                item.lower() for item in self.data["likes"]
            ]:
                self.data["likes"].append(like)

        self.save()

    # -------------------------
    # GETTERS
    # -------------------------

    def get_name(self):
        return self.data.get("name")

    def get_favorite_color(self):
        return self.data.get("favorite_color")

    def get_dog_name(self):
        return self.data.get("dog_name")

    def get_likes(self):
        return self.data.get("likes", [])