from abc import ABC, abstractmethod


class CloudProvider(ABC):
    """
    Base interface for Aether cloud AI providers.

    Cloud providers do not decide whether data is
    allowed to leave the machine.

    Aether's privacy gate must make that decision
    BEFORE a cloud provider is called.
    """

    provider_type = "cloud_ai"
    requires_permission = False

    @property
    @abstractmethod
    def name(
        self
    ):
        raise NotImplementedError

    @property
    def description(
        self
    ):

        return (
            "Cloud AI provider."
        )

    @abstractmethod
    def configured(
        self
    ):
        raise NotImplementedError

    @abstractmethod
    def available(
        self
    ):
        raise NotImplementedError

    @abstractmethod
    def capabilities(
        self
    ):
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        capability,
        task
    ):
        raise NotImplementedError

    def info(
        self
    ):

        return {
            "name": self.name,
            "description": (
                self.description
            ),
            "type": (
                self.provider_type
            ),
            "configured": (
                self.configured()
            ),
            "available": (
                self.available()
            ),
            "capabilities": (
                self.capabilities()
            ),
            "requires_permission": (
                self.requires_permission
            )
        }