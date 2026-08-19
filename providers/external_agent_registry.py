import shutil

from pathlib import Path

from providers.external_cli_provider import (
    ExternalCLIProvider
)


class ExternalAgentRegistry:
    """
    Discovers external agent CLIs that Aether may
    integrate with.

    Discovery does NOT grant execution permission.

    These definitions identify possible workers.
    Actual task execution remains under Aether's
    permission and workflow systems.
    """

    def __init__(
        self,
        project_directory=None
    ):

        if project_directory:

            self.project_directory = str(
                Path(
                    project_directory
                ).resolve()
            )

        else:

            self.project_directory = None

        self.definitions = [
            {
                "name": "claude_code",
                "executables": [
                    "claude"
                ],
                "description": (
                    "Claude Code command-line agent."
                )
            },
            {
                "name": "codex_cli",
                "executables": [
                    "codex"
                ],
                "description": (
                    "Codex-compatible command-line "
                    "coding agent."
                )
            },
            {
                "name": "hermes",
                "executables": [
                    "hermes"
                ],
                "description": (
                    "Hermes-compatible command-line "
                    "agent."
                )
            }
        ]

    # ---------------------------------
    # DISCOVER
    # ---------------------------------

    def discover(self):

        providers = []

        for definition in (
            self.definitions
        ):

            executable = (
                self._find_executable(
                    definition.get(
                        "executables",
                        []
                    )
                )
            )

            if executable is None:

                continue

            provider = (
                ExternalCLIProvider(
                    provider_name=(
                        definition["name"]
                    ),
                    executable=executable,
                    capabilities=[
                        "external_agent"
                    ],
                    description=(
                        definition[
                            "description"
                        ]
                    ),
                    working_directory=(
                        self.project_directory
                    )
                )
            )

            providers.append(
                provider
            )

        return providers

    # ---------------------------------
    # DISCOVERY REPORT
    # ---------------------------------

    def discovery_report(self):

        report = []

        for definition in (
            self.definitions
        ):

            executable = (
                self._find_executable(
                    definition.get(
                        "executables",
                        []
                    )
                )
            )

            report.append(
                {
                    "name": (
                        definition["name"]
                    ),
                    "installed": (
                        executable
                        is not None
                    ),
                    "executable": executable,
                    "description": (
                        definition[
                            "description"
                        ]
                    )
                }
            )

        return report

    # ---------------------------------
    # FIND EXECUTABLE
    # ---------------------------------

    def _find_executable(
        self,
        candidates
    ):

        for candidate in candidates:

            path = shutil.which(
                candidate
            )

            if path:

                return candidate

        return None