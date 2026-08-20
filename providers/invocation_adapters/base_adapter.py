from abc import ABC, abstractmethod


class BaseInvocationAdapter(ABC):
    """
    Converts an Aether delegation plan into a
    provider-specific command.

    Adapters build commands.

    They do NOT execute commands themselves.
    """

    name = "base"
    provider_name = None

    @abstractmethod
    def available(
        self
    ):
        raise NotImplementedError

    @abstractmethod
    def supports_role(
        self,
        role
    ):
        raise NotImplementedError

    @abstractmethod
    def build(
        self,
        task,
        role=None,
        options=None
    ):
        raise NotImplementedError

    def info(
        self
    ):

        return {
            "name": self.name,
            "provider": (
                self.provider_name
            ),
            "available": (
                self.available()
            )
        }