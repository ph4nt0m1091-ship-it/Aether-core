from abc import ABC, abstractmethod


class Mission(ABC):
    """
    Base class for every Aether mission.
    """

    keyword = ""
    name = ""

    @abstractmethod
    def build(self):
        pass