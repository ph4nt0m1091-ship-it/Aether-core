from providers.openrouter_provider import (
    OpenRouterProvider
)


class CloudProviderRegistry:
    """
    Registry for Aether cloud providers.

    Registration does NOT mean a provider may
    receive data.

    Privacy approval happens outside this layer.
    """

    def __init__(
        self
    ):

        self.providers = {}

        self.register(
            OpenRouterProvider()
        )

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
            None
        )

        if not name:

            return False

        self.providers[
            str(
                name
            ).strip().lower()
        ] = provider

        return True

    # ---------------------------------
    # GET
    # ---------------------------------

    def get(
        self,
        name
    ):

        if not name:

            return None

        return self.providers.get(
            str(
                name
            ).strip().lower()
        )

    # ---------------------------------
    # INFO
    # ---------------------------------

    def info(
        self
    ):

        return [
            provider.info()
            for provider in (
                self.providers.values()
            )
        ]

    # ---------------------------------
    # CONFIGURED
    # ---------------------------------

    def configured(
        self
    ):

        return [
            provider
            for provider in (
                self.providers.values()
            )
            if provider.configured()
        ]