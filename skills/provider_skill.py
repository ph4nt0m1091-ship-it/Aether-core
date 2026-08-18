from providers.aether_provider import AetherProvider
from providers.local_system_provider import LocalSystemProvider
from providers.ollama_provider import OllamaProvider
from providers.provider_manager import ProviderManager


class ProviderSkill:
    """
    Gives Aether visibility into its provider ecosystem.

    Current abilities:
    - Show available providers
    - Show provider capabilities
    - Show installed Ollama models
    - Send prompts to local Ollama models
    """

    name = "providers"

    description = (
        "Manages Aether's native, local-system, "
        "and external AI providers."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.manager = ProviderManager()

        self.manager.register(
            AetherProvider()
        )

        self.manager.register(
            LocalSystemProvider()
        )

        self.manager.register(
            OllamaProvider()
        )

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        message = message.strip()
        lower = message.lower()

        # ---------------------------------
        # SHOW PROVIDERS
        # ---------------------------------

        if lower in (
            "show providers",
            "list providers",
            "what providers do you have",
            "what providers are available"
        ):

            return self._show_providers()

        # ---------------------------------
        # SHOW CAPABILITIES
        # ---------------------------------

        if lower in (
            "show provider capabilities",
            "provider capabilities",
            "show capabilities"
        ):

            return self._show_capabilities()

        # ---------------------------------
        # OLLAMA MODELS
        # ---------------------------------

        if lower in (
            "show ollama models",
            "list ollama models",
            "ollama models",
            "what ollama models do i have"
        ):

            return self._show_ollama_models()

        # ---------------------------------
        # ASK OLLAMA
        # ---------------------------------

        prefix = "ask ollama "

        if lower.startswith(
            prefix
        ):

            request = message[
                len(prefix):
            ].strip()

            return self._ask_ollama(
                request
            )

        return None

    # ---------------------------------
    # SHOW PROVIDERS
    # ---------------------------------

    def _show_providers(
        self
    ):

        output = (
            "Aether: Provider Status\n\n"
        )

        if not self.manager.providers:

            return (
                "Aether: No providers "
                "are registered."
            )

        for provider in (
            self.manager
            .providers
            .values()
        ):

            available = (
                provider.available()
            )

            status = (
                "available"
                if available
                else "offline"
            )

            output += (
                f"- {provider.name}\n"
                f"  Status: {status}\n"
                f"  Description: "
                f"{provider.description}\n"
            )

            capabilities = (
                provider.capabilities()
            )

            if capabilities:

                output += (
                    "  Capabilities: "
                    + ", ".join(
                        capabilities
                    )
                    + "\n"
                )

            output += "\n"

        return output.rstrip()

    # ---------------------------------
    # CAPABILITIES
    # ---------------------------------

    def _show_capabilities(
        self
    ):

        capabilities = (
            self.manager
            .capabilities()
        )

        if not capabilities:

            return (
                "Aether: No provider "
                "capabilities are currently available."
            )

        output = (
            "Aether: Available Provider "
            "Capabilities\n\n"
        )

        for capability, providers in (
            capabilities.items()
        ):

            output += (
                f"- {capability}\n"
                f"  Providers: "
                f"{', '.join(providers)}\n"
            )

        return output.rstrip()

    # ---------------------------------
    # OLLAMA MODELS
    # ---------------------------------

    def _show_ollama_models(
        self
    ):

        result = self.manager.execute(
            "list_models",
            {},
            provider_name="ollama"
        )

        if not result.get(
            "success"
        ):

            return (
                "Aether: Ollama is unavailable.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        models = result.get(
            "models",
            []
        )

        if not models:

            return (
                "Aether: Ollama is running, "
                "but no local models were found."
            )

        output = (
            "Aether: Local Ollama Models\n\n"
        )

        for model in models:

            output += (
                f"- {model}\n"
            )

        return output.rstrip()

    # ---------------------------------
    # ASK OLLAMA
    # ---------------------------------

    def _ask_ollama(
        self,
        request
    ):

        if not request:

            return (
                "Aether: Tell me which Ollama "
                "model and prompt to use.\n\n"
                "Example:\n"
                "ask ollama qwen3:4b "
                "explain what a motor driver is"
            )

        model_result = self.manager.execute(
            "list_models",
            {},
            provider_name="ollama"
        )

        if not model_result.get(
            "success"
        ):

            return (
                "Aether: Ollama is unavailable.\n"
                f"{model_result.get('error', '')}"
            ).rstrip()

        installed_models = (
            model_result.get(
                "models",
                []
            )
        )

        # ---------------------------------
        # DETECT MODEL
        # ---------------------------------

        model = None
        prompt = request

        for installed_model in (
            installed_models
        ):

            prefix = (
                installed_model
                + " "
            )

            if request.lower().startswith(
                prefix.lower()
            ):

                model = (
                    installed_model
                )

                prompt = request[
                    len(prefix):
                ].strip()

                break

        # ---------------------------------
        # FALLBACK MODEL
        # ---------------------------------

        if model is None:

            preferred_models = [
                "qwen3:4b",
                "gemma3:1b",
                "qwen3:8b"
            ]

            for preferred in (
                preferred_models
            ):

                if preferred in installed_models:

                    model = preferred

                    break

            if (
                model is None
                and installed_models
            ):

                model = (
                    installed_models[0]
                )

        if model is None:

            return (
                "Aether: I couldn't find "
                "an installed Ollama model."
            )

        if not prompt:

            return (
                f"Aether: What would you like "
                f"me to ask {model}?"
            )

        # ---------------------------------
        # GENERATE
        # ---------------------------------

        result = self.manager.execute(
            "generate_text",
            {
                "model": model,
                "prompt": prompt
            },
            provider_name="ollama"
        )

        if not result.get(
            "success"
        ):

            return (
                "Aether: Ollama generation failed.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        response = result.get(
            "response",
            ""
        ).strip()

        if not response:

            response = (
                "The model returned "
                "an empty response."
            )

        return (
            f"Aether: Ollama response "
            f"from {model}:\n\n"
            f"{response}"
        )

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None