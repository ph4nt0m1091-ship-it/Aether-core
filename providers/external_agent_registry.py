import shutil

from pathlib import Path

from providers.agent_profile_registry import (
    AgentProfileRegistry
)

from providers.external_cli_provider import (
    ExternalCLIProvider
)


class ExternalAgentRegistry:
    """
    Discovers external-agent CLIs known to Aether.

    Agent identity and roles come from AgentProfileRegistry.

    Discovery does not grant execution permission.
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

        self.profile_registry = (
            AgentProfileRegistry()
        )

    # ---------------------------------
    # DISCOVER
    # ---------------------------------

    def discover(
        self
    ):

        providers = []

        for profile in (
            self.profile_registry
            .enabled()
        ):

            executable = (
                self._find_executable(
                    profile.executables
                )
            )

            if executable is None:

                continue

            provider = (
                ExternalCLIProvider(
                    provider_name=(
                        profile.name
                    ),
                    executable=(
                        executable
                    ),
                    capabilities=[
                        "external_agent"
                    ],
                    description=(
                        profile.description
                    ),
                    working_directory=(
                        self.project_directory
                    )
                )
            )

            provider.agent_profile = (
                profile
            )

            providers.append(
                provider
            )

        return providers

    # ---------------------------------
    # DISCOVERY REPORT
    # ---------------------------------

    def discovery_report(
        self
    ):

        report = []

        for profile in (
            self.profile_registry
            .enabled()
        ):

            executable = (
                self._find_executable(
                    profile.executables
                )
            )

            report.append(
                {
                    "name": (
                        profile.name
                    ),
                    "display_name": (
                        profile.display_name
                    ),
                    "installed": (
                        executable
                        is not None
                    ),
                    "executable": (
                        executable
                    ),
                    "description": (
                        profile.description
                    ),
                    "roles": list(
                        profile.roles
                    ),
                    "execution_type": (
                        profile.execution_type
                    ),
                    "requires_permission": (
                        profile
                        .requires_permission
                    ),
                    "local_model_support": (
                        profile
                        .local_model_support
                    ),
                    "cloud_support": (
                        profile.cloud_support
                    )
                }
            )

        return report

    # ---------------------------------
    # FIND BY ROLE
    # ---------------------------------

    def find_by_role(
        self,
        role,
        installed_only=True
    ):

        matches = []

        profiles = (
            self.profile_registry
            .find_by_role(
                role
            )
        )

        for profile in profiles:

            executable = (
                self._find_executable(
                    profile.executables
                )
            )

            if (
                installed_only
                and executable is None
            ):

                continue

            matches.append(
                {
                    "profile": (
                        profile
                    ),
                    "executable": (
                        executable
                    )
                }
            )

        return matches

    # ---------------------------------
    # FIND EXECUTABLE
    # ---------------------------------

    def _find_executable(
        self,
        candidates
    ):

        for candidate in (
            candidates or []
        ):

            path = shutil.which(
                candidate
            )

            if path:

                return candidate

        return None