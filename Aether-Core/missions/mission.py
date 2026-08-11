class Mission:
    """
    Base class for every Aether mission.
    """

    name = "Unnamed Mission"
    keyword = ""

    def build(self):
        raise NotImplementedError(
            "Every mission must implement build()."
        )