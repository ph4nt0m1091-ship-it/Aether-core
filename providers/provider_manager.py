class ProviderManager:
    """
    Registry and router for Aether capability providers.
    """

    def __init__(
        self
    ):

        self.providers = {}

    # ---------------------------------
    # REGISTER
    # ---------------------------------

    def register(
        self,
        provider
    ):

        if provider is None:

            return False

        name = getattr(
            provider,
            "name",
            ""
        ).strip()

        if not name:

            return False

        self.providers[
            name
        ] = provider

        return True

    # ---------------------------------
    # REGISTER MANY
    # ---------------------------------

    def register_many(
        self,
        providers
    ):

        registered = []

        for provider in (
            providers or []
        ):

            if self.register(
                provider
            ):

                registered.append(
                    provider.name
                )

        return registered

    # ---------------------------------
    # GET PROVIDER
    # ---------------------------------

    def get(
        self,
        name
    ):

        return self.providers.get(
            name
        )

    # ---------------------------------
    # PROVIDER INFO
    # ---------------------------------

    def provider_info(
        self
    ):

        return [
            provider.info()
            for provider in (
                self.providers.values()
            )
        ]

    # ---------------------------------
    # AVAILABLE PROVIDERS
    # ---------------------------------

    def available_providers(
        self
    ):

        return [
            provider.info()
            for provider in (
                self.providers.values()
            )
            if provider.available()
        ]

    # ---------------------------------
    # EXTERNAL AGENTS
    # ---------------------------------

    def external_agents(
        self
    ):

        agents = []

        for provider in (
            self.providers.values()
        ):

            if getattr(
                provider,
                "provider_type",
                ""
            ) != "external_agent":

                continue

            agents.append(
                provider.info()
            )

        return agents

    # ---------------------------------
    # ALL CAPABILITIES
    # ---------------------------------

    def capabilities(
        self
    ):

        capabilities = {}

        for name, provider in (
            self.providers.items()
        ):

            if not provider.available():

                continue

            for capability in (
                provider.capabilities()
            ):

                capabilities.setdefault(
                    capability,
                    []
                ).append(
                    name
                )

        return capabilities

    # ---------------------------------
    # FIND PROVIDERS
    # ---------------------------------

    def find_providers(
        self,
        capability
    ):

        matches = []

        for provider in (
            self.providers.values()
        ):

            if not provider.available():

                continue

            if capability in (
                provider.capabilities()
            ):

                matches.append(
                    provider
                )

        return matches

    # ---------------------------------
    # FIND PROVIDER
    # ---------------------------------

    def find_provider(
        self,
        capability
    ):

        matches = (
            self.find_providers(
                capability
            )
        )

        if not matches:

            return None

        return matches[0]

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        capability,
        task,
        provider_name=None
    ):

        if provider_name:

            provider = self.get(
                provider_name
            )

            if provider is None:

                return {
                    "success": False,
                    "error": (
                        f'Provider "{provider_name}" '
                        "was not found."
                    )
                }

            if not provider.available():

                return {
                    "success": False,
                    "provider": (
                        provider_name
                    ),
                    "error": (
                        f'Provider "{provider_name}" '
                        "is not available."
                    )
                }

        else:

            provider = (
                self.find_provider(
                    capability
                )
            )

        if provider is None:

            return {
                "success": False,
                "error": (
                    "No available provider supports "
                    f'"{capability}".'
                )
            }

        if capability not in (
            provider.capabilities()
        ):

            return {
                "success": False,
                "provider": (
                    provider.name
                ),
                "error": (
                    f'Provider "{provider.name}" '
                    f'does not support '
                    f'"{capability}".'
                )
            }

        result = provider.execute(
            capability,
            task
        )

        if not isinstance(
            result,
            dict
        ):

            result = {
                "success": False,
                "provider": (
                    provider.name
                ),
                "error": (
                    "Provider returned an "
                    "invalid result."
                )
            }

        result.setdefault(
            "provider",
            provider.name
        )

        result.setdefault(
            "provider_type",
            getattr(
                provider,
                "provider_type",
                "generic"
            )
        )

        result.setdefault(
            "capability",
            capability
        )

        result.setdefault(
            "requires_permission",
            getattr(
                provider,
                "requires_permission",
                False
            )
        )

        return result