from providers.base_provider import BaseProvider


class AetherProvider(BaseProvider):
    """
    Native Aether capabilities.

    This provider represents capabilities implemented
    directly inside Aether itself.
    """

    name = "aether"

    description = (
        "Native capabilities implemented by Aether."
    )

    def available(self):

        return True

    def capabilities(self):

        return [
            "research",
            "web_search"
        ]

    def execute(self, capability, task):

        return {
            "success": True,
            "provider": self.name,
            "capability": capability,
            "task": task,
            "status": "accepted"
        }