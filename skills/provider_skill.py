from model_router import ModelRouter
from resilience import ResiliencePolicy

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
    - Automatically route local AI requests
    - Explicitly select Ollama models
    - Retry temporary AI failures safely
    - Fall back to another local model when appropriate
    """

    name = "providers"

    description = (
        "Manages Aether's native, local-system, "
        "and external AI providers with resilient "
        "local-model execution."
    )

    MAX_PRIMARY_ATTEMPTS = 2

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.manager = ProviderManager()

        self.router = ModelRouter()

        self.resilience = ResiliencePolicy()

        self.last_execution_result = None

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

        self.last_execution_result = None

        message = message.strip()
        lower = message.lower()

        if lower in (
            "show providers",
            "list providers",
            "what providers do you have",
            "what providers are available"
        ):

            return self._show_providers()

        if lower in (
            "show provider capabilities",
            "provider capabilities",
            "show capabilities"
        ):

            return self._show_capabilities()

        if lower in (
            "show ollama models",
            "list ollama models",
            "ollama models",
            "what ollama models do i have"
        ):

            return self._show_ollama_models()

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
            self.manager.providers.values()
        ):

            available = provider.available()

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
    # SHOW CAPABILITIES
    # ---------------------------------

    def _show_capabilities(
        self
    ):

        capabilities = (
            self.manager.capabilities()
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
    # SHOW OLLAMA MODELS
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
                "Aether: Tell me what you "
                "would like the local AI to do."
            )

        # ---------------------------------
        # GET INSTALLED MODELS
        # ---------------------------------

        model_result = self.manager.execute(
            "list_models",
            {},
            provider_name="ollama"
        )

        if not model_result.get(
            "success"
        ):

            self.last_execution_result = (
                model_result
            )

            return (
                "Aether: Ollama is unavailable.\n"
                f"{model_result.get('error', '')}"
            ).rstrip()

        installed_models = model_result.get(
            "models",
            []
        )

        # ---------------------------------
        # EXPLICIT MODEL DETECTION
        # ---------------------------------

        requested_model = None
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

                requested_model = (
                    installed_model
                )

                prompt = request[
                    len(prefix):
                ].strip()

                break

        if not prompt:

            return (
                "Aether: What would you "
                "like the model to do?"
            )

        # ---------------------------------
        # ROUTE MODEL
        # ---------------------------------

        route = self.router.choose(
            prompt,
            installed_models,
            requested_model=(
                requested_model
            )
        )

        if not route.get(
            "success"
        ):

            self.last_execution_result = (
                route
            )

            return (
                "Aether: Model routing failed.\n"
                f"{route.get('error', '')}"
            ).rstrip()

        primary_model = route["model"]

        # ---------------------------------
        # PRIMARY ATTEMPTS
        # ---------------------------------

        attempts = []
        result = None

        for attempt_number in range(
            1,
            self.MAX_PRIMARY_ATTEMPTS + 1
        ):

            result = self._generate(
                route
            )

            attempts.append(
                {
                    "model": primary_model,
                    "attempt": attempt_number,
                    "success": result.get(
                        "success",
                        False
                    ),
                    "error": result.get(
                        "error"
                    )
                }
            )

            if result.get(
                "success"
            ):

                break

            if not self.resilience.can_retry(
                "generate_text",
                result
            ):

                break

        # ---------------------------------
        # FALLBACK MODEL
        # ---------------------------------

        fallback_used = False
        fallback_model = None

        if (
            result is not None
            and not result.get(
                "success",
                False
            )
            and self.resilience.can_retry(
                "generate_text",
                result
            )
        ):

            fallback_model = (
                self._choose_fallback_model(
                    primary_model,
                    installed_models
                )
            )

            if fallback_model:

                fallback_route = (
                    self.router.choose(
                        prompt,
                        installed_models,
                        requested_model=(
                            fallback_model
                        )
                    )
                )

                if fallback_route.get(
                    "success"
                ):

                    fallback_used = True

                    result = self._generate(
                        fallback_route
                    )

                    attempts.append(
                        {
                            "model": (
                                fallback_model
                            ),
                            "attempt": 1,
                            "success": result.get(
                                "success",
                                False
                            ),
                            "error": result.get(
                                "error"
                            ),
                            "fallback": True
                        }
                    )

                    if result.get(
                        "success"
                    ):

                        route = fallback_route

        # ---------------------------------
        # FINAL RESULT
        # ---------------------------------

        if result is None:

            result = {
                "success": False,
                "provider": "ollama",
                "error": (
                    "No Ollama generation "
                    "attempt was completed."
                )
            }

        result["attempts"] = attempts
        result["attempt_count"] = len(
            attempts
        )
        result["primary_model"] = (
            primary_model
        )
        result["fallback_used"] = (
            fallback_used
        )
        result["fallback_model"] = (
            fallback_model
        )
        result["failure_type"] = (
            self.resilience.classify(
                result
            )
        )

        self.last_execution_result = (
            result
        )

        # ---------------------------------
        # FAILURE
        # ---------------------------------

        if not result.get(
            "success"
        ):

            return (
                "Aether: Ollama generation failed.\n"
                f"{result.get('error', '')}\n\n"
                f"Attempts: "
                f"{result['attempt_count']}"
            ).rstrip()

        # ---------------------------------
        # SUCCESS
        # ---------------------------------

        response = result.get(
            "response",
            ""
        ).strip()

        if not response:

            response = (
                "The model returned "
                "an empty response."
            )

        output = (
            "Aether: Local AI response\n"
            f"Model: {route['model']}\n"
            f"Tier: {route['tier']}\n"
            f"Attempts: "
            f"{result['attempt_count']}"
        )

        if fallback_used:

            output += (
                "\nFallback: "
                f"{fallback_model}"
            )

        output += (
            "\n\n"
            + response
        )

        return output

    # ---------------------------------
    # GENERATE
    # ---------------------------------

    def _generate(
        self,
        route
    ):

        return self.manager.execute(
            "generate_text",
            {
                "model": route["model"],
                "prompt": route["prompt"],
                "think": route["think"],
                "num_ctx": route["num_ctx"],
                "num_predict": (
                    route["num_predict"]
                ),
                "keep_alive": (
                    route["keep_alive"]
                )
            },
            provider_name="ollama"
        )

    # ---------------------------------
    # FALLBACK MODEL
    # ---------------------------------

    def _choose_fallback_model(
        self,
        primary_model,
        installed_models
    ):

        candidates = [
            "gemma3:1b",
            "qwen3:4b"
        ]

        for model in candidates:

            if (
                model in installed_models
                and model != primary_model
            ):

                return model

        return None

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None