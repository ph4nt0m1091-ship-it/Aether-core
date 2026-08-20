class AgentProfile:
    """
    Describes an external agent that Aether may use.

    Profiles describe what an agent is for without
    directly executing it.

    Execution remains the responsibility of providers
    and Aether's permission system.
    """

    def __init__(
        self,
        name,
        display_name,
        description,
        executables=None,
        roles=None,
        execution_type="cli",
        requires_permission=True,
        local_model_support=False,
        cloud_support=False,
        enabled=True
    ):

        self.name = str(
            name
        ).strip()

        self.display_name = str(
            display_name
        ).strip()

        self.description = str(
            description
        ).strip()

        self.executables = (
            list(executables)
            if isinstance(
                executables,
                list
            )
            else []
        )

        self.roles = (
            list(roles)
            if isinstance(
                roles,
                list
            )
            else []
        )

        self.execution_type = (
            execution_type
        )

        self.requires_permission = bool(
            requires_permission
        )

        self.local_model_support = bool(
            local_model_support
        )

        self.cloud_support = bool(
            cloud_support
        )

        self.enabled = bool(
            enabled
        )

    # ---------------------------------
    # DICTIONARY
    # ---------------------------------

    def to_dict(
        self
    ):

        return {
            "name": self.name,
            "display_name": (
                self.display_name
            ),
            "description": (
                self.description
            ),
            "executables": list(
                self.executables
            ),
            "roles": list(
                self.roles
            ),
            "execution_type": (
                self.execution_type
            ),
            "requires_permission": (
                self.requires_permission
            ),
            "local_model_support": (
                self.local_model_support
            ),
            "cloud_support": (
                self.cloud_support
            ),
            "enabled": (
                self.enabled
            )
        }