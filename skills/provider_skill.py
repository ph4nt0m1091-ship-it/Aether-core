import shlex

from model_router import ModelRouter
from resilience import ResiliencePolicy

from permissions.permission_manager import (
    PermissionManager
)

from providers.aether_provider import (
    AetherProvider
)

from providers.external_agent_registry import (
    ExternalAgentRegistry
)

from providers.local_system_provider import (
    LocalSystemProvider
)

from providers.ollama_provider import (
    OllamaProvider
)

from providers.provider_manager import (
    ProviderManager
)


class ProviderSkill:
    """
    Manages Aether's provider ecosystem.

    Supports:
    - Native providers
    - Local-system providers
    - Ollama models
    - External-agent discovery
    - External-agent inspection
    - External-agent command previews
    - Permission-gated external-agent execution
    - Resilient Ollama retries and fallback
    """

    name = "providers"

    description = (
        "Manages Aether's native, local-system, "
        "local-AI, and external-agent providers."
    )

    MAX_PRIMARY_ATTEMPTS = 2

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.manager = (
            ProviderManager()
        )

        self.router = (
            ModelRouter()
        )

        self.resilience = (
            ResiliencePolicy()
        )

        self.permissions = (
            PermissionManager()
        )

        self.external_registry = (
            ExternalAgentRegistry(
                "."
            )
        )

        self.last_execution_result = None

        # ---------------------------------
        # CORE PROVIDERS
        # ---------------------------------

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
        # DISCOVER EXTERNAL AGENTS
        # ---------------------------------

        discovered = (
            self.external_registry
            .discover()
        )

        self.manager.register_many(
            discovered
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

        # ---------------------------------
        # PENDING EXTERNAL AGENT PERMISSION
        # ---------------------------------

        if self.permissions.has_pending():

            response = (
                self.permissions
                .interpret_response(
                    message
                )
            )

            if response == "approve":

                pending = (
                    self.permissions
                    .consume()
                )

                data = (
                    pending.get(
                        "data",
                        {}
                    )
                )

                provider_name = (
                    data.get(
                        "provider",
                        ""
                    )
                )

                args = (
                    data.get(
                        "args",
                        []
                    )
                )

                return (
                    self._execute_external_agent(
                        provider_name,
                        args
                    )
                )

            if response == "deny":

                self.permissions.cancel()

                return (
                    "Aether: External agent "
                    "execution cancelled."
                )

            return (
                "Aether: I am waiting for permission.\n"
                'Say "yes" to approve or "no" to cancel.'
            )

        # ---------------------------------
        # PROVIDER STATUS
        # ---------------------------------

        if lower in (
            "show providers",
            "list providers",
            "what providers do you have",
            "what providers are available"
        ):

            return (
                self._show_providers()
            )

        if lower in (
            "show provider capabilities",
            "provider capabilities",
            "show capabilities"
        ):

            return (
                self._show_capabilities()
            )

        # ---------------------------------
        # EXTERNAL AGENTS
        # ---------------------------------

        if lower in (
            "show external agents",
            "list external agents",
            "external agents",
            "what external agents do you have"
        ):

            return (
                self._show_external_agents()
            )

        info_prefixes = (
            "external agent info ",
            "show agent info ",
            "agent info "
        )

        for prefix in info_prefixes:

            if lower.startswith(
                prefix
            ):

                provider_name = (
                    message[
                        len(prefix):
                    ]
                    .strip()
                )

                return (
                    self._external_agent_info(
                        provider_name
                    )
                )

        preview_prefixes = (
            "preview agent ",
            "preview external agent "
        )

        for prefix in preview_prefixes:

            if lower.startswith(
                prefix
            ):

                request = (
                    message[
                        len(prefix):
                    ]
                    .strip()
                )

                return (
                    self._preview_external_request(
                        request
                    )
                )

        run_prefixes = (
            "run agent ",
            "run external agent "
        )

        for prefix in run_prefixes:

            if lower.startswith(
                prefix
            ):

                request = (
                    message[
                        len(prefix):
                    ]
                    .strip()
                )

                return (
                    self._request_external_execution(
                        request
                    )
                )

        # ---------------------------------
        # OLLAMA
        # ---------------------------------

        if lower in (
            "show ollama models",
            "list ollama models",
            "ollama models",
            "what ollama models do i have"
        ):

            return (
                self._show_ollama_models()
            )

        local_ai_prefixes = (
            "ask local ",
            "ask ollama ",
            "use local ai ",
            "use ollama "
        )

        for prefix in local_ai_prefixes:

            if lower.startswith(
                prefix
            ):

                request = (
                    message[
                        len(prefix):
                    ]
                    .strip()
                )

                return (
                    self._ask_ollama(
                        request
                    )
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

            available = (
                provider.available()
            )

            status = (
                "available"
                if available
                else "offline"
            )

            info = (
                provider.info()
            )

            output += (
                f"- {provider.name}\n"
                f"  Type: "
                f"{info.get('type', 'generic')}\n"
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

            if info.get(
                "requires_permission"
            ):

                output += (
                    "  Permission: required\n"
                )

            output += "\n"

        return (
            output.rstrip()
        )

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

        return (
            output.rstrip()
        )

    # ---------------------------------
    # SHOW EXTERNAL AGENTS
    # ---------------------------------

    def _show_external_agents(
        self
    ):

        report = (
            self.external_registry
            .discovery_report()
        )

        output = (
            "Aether: External Agent Discovery\n\n"
        )

        for item in report:

            status = (
                "installed"
                if item.get(
                    "installed"
                )
                else "not installed"
            )

            output += (
                f"- {item.get('name')}\n"
                f"  Status: {status}\n"
                f"  Description: "
                f"{item.get('description')}\n"
            )

            executable = (
                item.get(
                    "executable"
                )
            )

            if executable:

                output += (
                    f"  Executable: "
                    f"{executable}\n"
                )

            output += "\n"

        output += (
            "External-agent execution requires "
            "explicit permission."
        )

        return (
            output.rstrip()
        )

    # ---------------------------------
    # EXTERNAL AGENT INFO
    # ---------------------------------

    def _external_agent_info(
        self,
        provider_name
    ):

        provider_name = (
            provider_name.strip()
        )

        if not provider_name:

            return (
                "Aether: Which external "
                "agent should I inspect?"
            )

        provider = (
            self.manager.get(
                provider_name
            )
        )

        if provider is None:

            return (
                "Aether: External agent "
                f'"{provider_name}" '
                "is not registered."
            )

        if getattr(
            provider,
            "provider_type",
            ""
        ) != "external_agent":

            return (
                f'Aether: "{provider_name}" '
                "is not an external-agent provider."
            )

        info = (
            provider.info()
        )

        output = (
            "Aether: External Agent\n\n"
            f"Name: {info.get('name')}\n"
            f"Available: "
            f"{info.get('available')}\n"
            f"Executable: "
            f"{info.get('executable')}\n"
            f"Executable path: "
            f"{info.get('executable_path')}\n"
            f"Working directory: "
            f"{info.get('working_directory')}\n"
            "Permission required: "
            f"{info.get('requires_permission')}\n"
            "Capabilities: "
            f"{', '.join(info.get('capabilities', []))}"
        )

        return output

    # ---------------------------------
    # PARSE EXTERNAL REQUEST
    # ---------------------------------

    def _parse_external_request(
        self,
        request
    ):

        request = (
            request.strip()
        )

        if not request:

            return {
                "success": False,
                "error": (
                    "No external agent "
                    "request was provided."
                )
            }

        if " -- " in request:

            provider_name, raw_args = (
                request.split(
                    " -- ",
                    1
                )
            )

        else:

            provider_name = (
                request
            )

            raw_args = ""

        provider_name = (
            provider_name.strip()
        )

        if not provider_name:

            return {
                "success": False,
                "error": (
                    "No external agent "
                    "name was provided."
                )
            }

        try:

            args = (
                shlex.split(
                    raw_args,
                    posix=False
                )
                if raw_args
                else []
            )

        except ValueError as error:

            return {
                "success": False,
                "error": (
                    "External-agent arguments "
                    f"could not be parsed: {error}"
                )
            }

        cleaned_args = []

        for arg in args:

            arg = (
                str(arg)
                .strip()
            )

            if (
                len(arg) >= 2
                and arg[0] == arg[-1]
                and arg[0] in (
                    '"',
                    "'"
                )
            ):

                arg = arg[
                    1:-1
                ]

            cleaned_args.append(
                arg
            )

        return {
            "success": True,
            "provider": provider_name,
            "args": cleaned_args
        }

    # ---------------------------------
    # PREVIEW EXTERNAL REQUEST
    # ---------------------------------

    def _preview_external_request(
        self,
        request
    ):

        parsed = (
            self._parse_external_request(
                request
            )
        )

        if not parsed.get(
            "success"
        ):

            return (
                "Aether: "
                + parsed.get(
                    "error",
                    "Invalid external-agent request."
                )
            )

        provider_name = (
            parsed["provider"]
        )

        provider = (
            self.manager.get(
                provider_name
            )
        )

        if provider is None:

            return (
                "Aether: External agent "
                f'"{provider_name}" '
                "is not registered."
            )

        if getattr(
            provider,
            "provider_type",
            ""
        ) != "external_agent":

            return (
                f'Aether: "{provider_name}" '
                "is not an external agent."
            )

        command = (
            provider.preview_command(
                {
                    "args": (
                        parsed["args"]
                    )
                }
            )
        )

        return (
            "Aether: External Agent Preview\n\n"
            f"Provider: {provider_name}\n"
            f"Available: {provider.available()}\n"
            "Permission required: yes\n"
            f"Command: {command}\n\n"
            "Nothing was executed."
        )

    # ---------------------------------
    # REQUEST EXTERNAL EXECUTION
    # ---------------------------------

    def _request_external_execution(
        self,
        request
    ):

        parsed = (
            self._parse_external_request(
                request
            )
        )

        if not parsed.get(
            "success"
        ):

            return (
                "Aether: "
                + parsed.get(
                    "error",
                    "Invalid external-agent request."
                )
            )

        provider_name = (
            parsed["provider"]
        )

        provider = (
            self.manager.get(
                provider_name
            )
        )

        if provider is None:

            return (
                "Aether: External agent "
                f'"{provider_name}" '
                "is not registered."
            )

        if getattr(
            provider,
            "provider_type",
            ""
        ) != "external_agent":

            return (
                f'Aether: "{provider_name}" '
                "is not an external agent."
            )

        if not provider.available():

            return (
                "Aether: External agent "
                f'"{provider_name}" '
                "is currently unavailable."
            )

        args = (
            parsed["args"]
        )

        command = (
            provider.preview_command(
                {
                    "args": args
                }
            )
        )

        self.permissions.request(
            "external_agent_execution",
            {
                "provider": (
                    provider_name
                ),
                "args": args
            }
        )

        return (
            "Aether: Permission required.\n\n"
            f"External agent: "
            f"{provider_name}\n"
            f"Command: {command}\n\n"
            "External agents may read or modify "
            "project files depending on their "
            "arguments and capabilities.\n\n"
            'Say "yes" to approve or '
            '"no" to cancel.'
        )

    # ---------------------------------
    # EXECUTE EXTERNAL AGENT
    # ---------------------------------

    def _execute_external_agent(
        self,
        provider_name,
        args
    ):

        result = (
            self.manager.execute(
                "external_agent",
                {
                    "args": args
                },
                provider_name=(
                    provider_name
                )
            )
        )

        self.last_execution_result = (
            result
        )

        if not result.get(
            "success"
        ):

            error = (
                result.get(
                    "stderr"
                )
                or result.get(
                    "error"
                )
                or (
                    "External agent "
                    "execution failed."
                )
            )

            return (
                "Aether: External agent failed.\n\n"
                f"Provider: {provider_name}\n"
                f"{error}"
            )

        output = (
            result.get(
                "stdout",
                ""
            )
            or result.get(
                "response",
                ""
            )
        )

        if len(output) > 8000:

            output = (
                output[:8000]
                + "\n\n[Output truncated]"
            )

        if not output:

            output = (
                "External agent completed "
                "without text output."
            )

        return (
            "Aether: External agent completed.\n\n"
            f"Provider: {provider_name}\n\n"
            f"{output}"
        )

    # ---------------------------------
    # SHOW OLLAMA MODELS
    # ---------------------------------

    def _show_ollama_models(
        self
    ):

        result = (
            self.manager.execute(
                "list_models",
                {},
                provider_name="ollama"
            )
        )

        if not result.get(
            "success"
        ):

            return (
                "Aether: Ollama is unavailable.\n"
                f"{result.get('error', '')}"
            ).rstrip()

        models = (
            result.get(
                "models",
                []
            )
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

        return (
            output.rstrip()
        )

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

        model_result = (
            self.manager.execute(
                "list_models",
                {},
                provider_name="ollama"
            )
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

        installed_models = (
            model_result.get(
                "models",
                []
            )
        )

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

                prompt = (
                    request[
                        len(prefix):
                    ]
                    .strip()
                )

                break

        if not prompt:

            return (
                "Aether: What would you "
                "like the model to do?"
            )

        route = (
            self.router.choose(
                prompt,
                installed_models,
                requested_model=(
                    requested_model
                )
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

        primary_model = (
            route["model"]
        )

        attempts = []
        result = None

        for attempt_number in range(
            1,
            self.MAX_PRIMARY_ATTEMPTS + 1
        ):

            result = (
                self._generate(
                    route
                )
            )

            attempts.append(
                {
                    "model": primary_model,
                    "attempt": (
                        attempt_number
                    ),
                    "success": (
                        result.get(
                            "success",
                            False
                        )
                    ),
                    "error": (
                        result.get(
                            "error"
                        )
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

                    result = (
                        self._generate(
                            fallback_route
                        )
                    )

                    attempts.append(
                        {
                            "model": (
                                fallback_model
                            ),
                            "attempt": 1,
                            "success": (
                                result.get(
                                    "success",
                                    False
                                )
                            ),
                            "error": (
                                result.get(
                                    "error"
                                )
                            ),
                            "fallback": True
                        }
                    )

                    if result.get(
                        "success"
                    ):

                        route = (
                            fallback_route
                        )

        if result is None:

            result = {
                "success": False,
                "provider": "ollama",
                "error": (
                    "No Ollama generation "
                    "attempt was completed."
                )
            }

        result[
            "attempts"
        ] = attempts

        result[
            "attempt_count"
        ] = len(
            attempts
        )

        result[
            "primary_model"
        ] = primary_model

        result[
            "fallback_used"
        ] = fallback_used

        result[
            "fallback_model"
        ] = fallback_model

        result[
            "failure_type"
        ] = (
            self.resilience.classify(
                result
            )
        )

        self.last_execution_result = (
            result
        )

        if not result.get(
            "success"
        ):

            return (
                "Aether: Ollama generation failed.\n"
                f"{result.get('error', '')}\n\n"
                f"Attempts: "
                f"{result['attempt_count']}"
            ).rstrip()

        response = (
            result.get(
                "response",
                ""
            )
            .strip()
        )

        response = (
            self._clean_local_ai_response(
                response
            )
        )

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
    # CLEAN LOCAL AI RESPONSE
    # ---------------------------------

    def _clean_local_ai_response(
        self,
        response
    ):

        """
        Remove internal reasoning markers that
        some local models may return even when
        thinking is disabled.

        This only changes displayed text.
        It does not modify model routing,
        provider execution, retries, or fallback.
        """

        text = str(
            response or ""
        ).strip()

        if not text:

            return ""

        # ---------------------------------
        # COMPLETE <think>...</think> BLOCKS
        # ---------------------------------

        while True:

            lower = (
                text.lower()
            )

            start = (
                lower.find(
                    "<think>"
                )
            )

            if start == -1:

                break

            end = (
                lower.find(
                    "</think>",
                    start
                )
            )

            if end == -1:

                # An opening think marker without
                # a closing marker means the rest
                # is likely internal reasoning.
                text = (
                    text[:start]
                    .strip()
                )

                break

            end += len(
                "</think>"
            )

            text = (
                text[:start]
                + text[end:]
            ).strip()

        # ---------------------------------
        # ORPHAN </think> MARKER
        # ---------------------------------

        lower = (
            text.lower()
        )

        closing = (
            lower.rfind(
                "</think>"
            )
        )

        if closing != -1:

            # Some Qwen responses expose reasoning
            # followed by only the closing marker.
            #
            # In that case the useful final answer
            # is normally after </think>.
            after = (
                text[
                    closing
                    + len("</think>"):
                ]
                .strip()
            )

            if after:

                text = after

            else:

                text = (
                    text[:closing]
                    .strip()
                )

        # ---------------------------------
        # REMOVE STRAY OPENING MARKERS
        # ---------------------------------

        text = (
            text.replace(
                "<think>",
                ""
            )
            .replace(
                "<THINK>",
                ""
            )
            .strip()
        )

        return text

    # ---------------------------------
    # GENERATE
    # ---------------------------------

    def _generate(
        self,
        route
    ):

        return (
            self.manager.execute(
                "generate_text",
                {
                    "model": (
                        route["model"]
                    ),
                    "prompt": (
                        route["prompt"]
                    ),
                    "think": (
                        route["think"]
                    ),
                    "num_ctx": (
                        route["num_ctx"]
                    ),
                    "num_predict": (
                        route["num_predict"]
                    ),
                    "keep_alive": (
                        route["keep_alive"]
                    )
                },
                provider_name="ollama"
            )
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