import inspect

from missions.discover import discover_modules
from missions.mission import Mission


def load_missions():
    """
    Discovers and loads every mission automatically.
    """

    loaded = []

    for module in discover_modules():

        for _, obj in inspect.getmembers(module, inspect.isclass):

            if (
                issubclass(obj, Mission)
                and obj is not Mission
            ):

                loaded.append(obj())

    return loaded