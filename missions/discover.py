import importlib
import pkgutil

import missions


def discover_modules():
    """
    Returns every mission module inside the missions package.
    """

    modules = []

    for _, module_name, _ in pkgutil.iter_modules(missions.__path__):

        if module_name in (
            "mission",
            "registry",
            "loader",
            "__init__",
            "discover"
        ):
            continue

        module = importlib.import_module(
            f"missions.{module_name}"
        )

        modules.append(module)

    return modules