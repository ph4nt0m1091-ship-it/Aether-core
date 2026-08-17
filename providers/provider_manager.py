class ProviderManager:
    """
    Registry and router for Aether capability providers.
    """

    def __init__(self):

        self.providers = {}

    # ---------------------------------
    # REGISTER
    # ---------------------------------

    def register(self, provider):

        if provider is None:

            return False

        name = getattr(
            provider,
            "name",
            ""
        ).strip()

        if not name:

            return False

        self.providers[name] = provider

        return True

    # ---------------------------------
    # GET PROVIDER
    # ---------------------------------

    def get(self, name):

        return self.providers.get(
            name
        )

    # ---------------------------------
    # AVAILABLE PROVIDERS
    # ---------------------------------

    def available_providers(self):

        return [
            provider.info()
            for provider in self.providers.values()
            if provider.available()
        ]

    # ---------------------------------
    # ALL CAPABILITIES
    # ---------------------------------

    def capabilities(self):

        capabilities = {}

        for name, provider in self.providers.items():

            if not provider.available():

                continue

            for capability in provider.capabilities():

                capabilities.setdefault(
                    capability,
                    []
                ).append(
                    name
                )

        return capabilities

    # ---------------------------------
    # FIND PROVIDER
    # ---------------------------------

    def find_provider(self, capability):

        for provider in self.providers.values():

            if not provider.available():

                continue

            if capability in provider.capabilities():

                return provider

        return None

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
                    "error": (
                        f'Provider "{provider_name}" '
                        "is not available."
                    )
                }

        else:

            provider = self.find_provider(
                capability
            )

        if provider is None:

            return {
                "success": False,
                "error": (
                    "No available provider supports "
                    f'"{capability}".'
                )
            }

        if capability not in provider.capabilities():

            return {
                "success": False,
                "error": (
                    f'Provider "{provider.name}" does not '
                    f'support "{capability}".'
                )
            }

        return provider.execute(
            capability,
            task
        )