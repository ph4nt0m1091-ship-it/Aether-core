from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """
    Base interface for external capability providers.

    Providers allow Aether to delegate work to other
    agents, models, applications, or execution systems.
    """

    name = "provider"

    description = "Generic Aether provider."

    @abstractmethod
    def available(self):
        """
        Return True when this provider can currently be used.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self):
        """
        Return a list of capabilities exposed by this provider.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, capability, task):
        """
        Execute one capability.

        Providers should return structured data whenever possible.
        """
        raise NotImplementedError

    def info(self):
        """
        Return provider metadata.
        """

        return {
            "name": self.name,
            "description": self.description,
            "available": self.available(),
            "capabilities": self.capabilities()
        }