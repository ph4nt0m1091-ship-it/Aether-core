from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """
    Base interface for Aether capability providers.

    Providers allow Aether to delegate work to models,
    agents, applications, services, or execution systems.
    """

    name = "provider"

    description = "Generic Aether provider."

    provider_type = "generic"

    requires_permission = False

    # ---------------------------------
    # AVAILABLE
    # ---------------------------------

    @abstractmethod
    def available(self):
        """
        Return True when this provider can currently be used.
        """

        raise NotImplementedError

    # ---------------------------------
    # CAPABILITIES
    # ---------------------------------

    @abstractmethod
    def capabilities(self):
        """
        Return capabilities exposed by this provider.
        """

        raise NotImplementedError

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    @abstractmethod
    def execute(
        self,
        capability,
        task
    ):
        """
        Execute a capability.

        Providers should return structured data.
        """

        raise NotImplementedError

    # ---------------------------------
    # INFO
    # ---------------------------------

    def info(self):
        """
        Return structured provider metadata.
        """

        return {
            "name": self.name,
            "description": self.description,
            "type": self.provider_type,
            "available": self.available(),
            "capabilities": self.capabilities(),
            "requires_permission": (
                self.requires_permission
            )
        }