from permissions.permission_manager import (
    PermissionManager
)

from policies.cloud_side_mode import (
    CloudSideMode
)

from policies.cloud_request_guard import (
    CloudRequestGuard
)

from policies.cloud_usage_tracker import (
    CloudUsageTracker
)

from policies.cloud_routing_policy import (
    CloudRoutingPolicy
)

from policies.local_cloud_advisor import (
    LocalCloudAdvisor
)

from providers.cloud_provider_registry import (
    CloudProviderRegistry
)

from providers.ollama_provider import (
    OllamaProvider
)


class CloudSideModeSkill:
    """
    Aether Cloud Side Mode.

    Safety stack:
    - local by default
    - explicit cloud requests only
    - privacy gate
    - configured provider requirement
    - user permission gate
    - rate guard
    - provider free-model guard
    - safe cloud usage visibility
    - advisory cloud routing intelligence
    - local versus cloud advisor
    - dynamic local Ollama model discovery
    """

    name = "cloud_side_mode"

    description = (
        "Controls Aether's privacy-gated, "
        "permission-gated, rate-limited "
        "cloud side mode and routing advisors."
    )

    def __init__(
        self,
        memory
    ):

        self.memory = memory

        self.cloud = (
            CloudSideMode()
        )

        self.providers = (
            CloudProviderRegistry()
        )

        self.ollama_provider = (
            OllamaProvider()
        )

        self.permissions = (
            PermissionManager()
        )

        self.request_guard = (
            CloudRequestGuard(
                max_requests=5,
                window_seconds=60
            )
        )

        self.usage_tracker = (
            CloudUsageTracker()
        )

        self.routing_policy = (
            CloudRoutingPolicy()
        )

        self.local_cloud_advisor = (
            LocalCloudAdvisor()
        )

        self.last_evaluation = None

        self.last_cloud_result = None

        self.cloud_execution_enabled = True

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        self.last_cloud_result = None

        message = str(
            message or ""
        ).strip()

        lower = (
            message.lower()
        )

        # ---------------------------------
        # PENDING PERMISSION
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

                return (
                    self._handle_approval(
                        pending
                    )
                )

            if response == "deny":

                self.permissions.cancel()

                return (
                    "Aether: Cloud request cancelled.\n\n"
                    "Nothing was sent."
                )

            return (
                "Aether: I am waiting for cloud "
                "permission.\n"
                'Say "yes" to approve or '
                '"no" to cancel.'
            )

        # ---------------------------------
        # ROUTE ADVISOR
        # ---------------------------------

        route_prefixes = (
            "cloud route ",
            "route cloud ",
            "cloud routing "
        )

        route_prefix = None

        for prefix in route_prefixes:

            if lower.startswith(
                prefix
            ):

                route_prefix = prefix

                break

        if route_prefix is not None:

            request = (
                message[
                    len(
                        route_prefix
                    ):
                ]
                .strip()
            )

            return (
                self._show_route(
                    request
                )
            )

        # ---------------------------------
        # LOCAL VS CLOUD ADVISOR
        # ---------------------------------

        compare_prefixes = (
            "compare route ",
            "local vs cloud ",
            "compare local cloud "
        )

        compare_prefix = None

        for prefix in compare_prefixes:

            if lower.startswith(
                prefix
            ):

                compare_prefix = prefix

                break

        if compare_prefix is not None:

            request = (
                message[
                    len(
                        compare_prefix
                    ):
                ]
                .strip()
            )

            return (
                self._show_local_cloud_advice(
                    request
                )
            )

        # ---------------------------------
        # LOCAL MODELS
        # ---------------------------------

        if lower in (
            "local models",
            "show local models",
            "ollama models",
            "show ollama models"
        ):

            return (
                self._show_local_models()
            )

        # ---------------------------------
        # STATUS
        # ---------------------------------

        if lower in (
            "cloud status",
            "show cloud status",
            "cloud mode status"
        ):

            return (
                self._show_status()
            )

        # ---------------------------------
        # PROVIDERS
        # ---------------------------------

        if lower in (
            "cloud providers",
            "show cloud providers",
            "list cloud providers",
            "show cloud provider",
            "cloud provider status"
        ):

            return (
                self._show_providers()
            )

        # ---------------------------------
        # GUARD
        # ---------------------------------

        if lower in (
            "cloud guard",
            "cloud guard status",
            "show cloud guard"
        ):

            return (
                self._show_guard()
            )

        # ---------------------------------
        # USAGE
        # ---------------------------------

        if lower in (
            "cloud usage",
            "show cloud usage",
            "cloud usage status"
        ):

            return (
                self._show_usage()
            )

        # ---------------------------------
        # ENABLE CLOUD SIDE MODE
        # ---------------------------------

        if lower in (
            "use cloud",
            "enable cloud",
            "enable cloud mode",
            "cloud mode on"
        ):

            self.cloud.use_cloud()

            return (
                "Aether: Cloud Side Mode enabled.\n\n"
                "Normal Aether requests remain local.\n"
                "Cloud is only used when explicitly "
                "requested.\n\n"
                "Privacy gate: active\n"
                "Permission gate: active\n"
                "Request guard: active\n"
                "Usage visibility: active\n"
                "Route advisor: active\n"
                "Local vs cloud advisor: active\n"
                "Dynamic local model discovery: active\n"
                "Cloud execution: enabled"
            )

        # ---------------------------------
        # LOCAL MODE
        # ---------------------------------

        if lower in (
            "use local",
            "local mode",
            "disable cloud",
            "disable cloud mode",
            "cloud mode off"
        ):

            self.cloud.use_local()

            return (
                "Aether: Local mode enabled.\n\n"
                "Cloud Side Mode is off."
            )

        # ---------------------------------
        # EXPLICIT CLOUD REQUEST
        # ---------------------------------

        prefixes = (
            "ask cloud ",
            "ask the cloud ",
            "use cloud for ",
            "send to cloud "
        )

        matched_prefix = None

        for prefix in prefixes:

            if lower.startswith(
                prefix
            ):

                matched_prefix = (
                    prefix
                )

                break

        if matched_prefix is None:

            return None

        request = (
            message[
                len(
                    matched_prefix
                ):
            ]
            .strip()
        )

        if not request:

            return (
                "Aether: What would you like "
                "the cloud to do?"
            )

        evaluation = (
            self.cloud.evaluate(
                request,
                explicit_cloud_request=True
            )
        )

        self.last_evaluation = (
            evaluation
        )

        return (
            self._handle_cloud_request(
                request,
                evaluation
            )
        )

    # ---------------------------------
    # DISCOVER LOCAL MODELS
    # ---------------------------------

    def _discover_local_models(
        self
    ):

        result = (
            self.ollama_provider.execute(
                "list_models",
                {}
            )
        )

        if not isinstance(
            result,
            dict
        ):

            return {
                "success": False,
                "models": [],
                "error": (
                    "Ollama returned an invalid response."
                )
            }

        if not result.get(
            "success"
        ):

            return {
                "success": False,
                "models": [],
                "error": (
                    result.get(
                        "error",
                        "Unable to discover Ollama models."
                    )
                )
            }

        models = (
            result.get(
                "models",
                []
            )
        )

        models = [
            str(
                model
            ).strip()
            for model in models
            if str(
                model
            ).strip()
        ]

        return {
            "success": True,
            "models": models,
            "error": None
        }

    # ---------------------------------
    # SHOW LOCAL MODELS
    # ---------------------------------

    def _show_local_models(
        self
    ):

        discovery = (
            self._discover_local_models()
        )

        if not discovery.get(
            "success"
        ):

            return (
                "Aether: Local Model Discovery\n\n"
                "Ollama model discovery failed.\n\n"
                f"Reason: "
                f"{discovery.get('error')}\n\n"
                "Nothing was executed."
            )

        models = (
            discovery.get(
                "models",
                []
            )
        )

        if not models:

            return (
                "Aether: Local Model Discovery\n\n"
                "Ollama is reachable, but no local "
                "models were found.\n\n"
                "Nothing was executed."
            )

        output = (
            "Aether: Local Model Discovery\n\n"
            "Installed Ollama models:\n"
        )

        for model in models:

            output += (
                f"- {model}\n"
            )

        output += (
            "\nSource: live local Ollama model list\n"
            "Model execution: none"
        )

        return (
            output.rstrip()
        )

    # ---------------------------------
    # ROUTE ADVISOR
    # ---------------------------------

    def _show_route(
        self,
        request
    ):

        if not request:

            return (
                "Aether: What request would you "
                "like me to evaluate for routing?"
            )

        decision = (
            self.routing_policy
            .decide(
                request
            )
        )

        route = str(
            decision.get(
                "route",
                "local"
            )
        ).strip()

        reason = str(
            decision.get(
                "reason",
                "unknown"
            )
        ).strip()

        explicit_cloud = bool(
            decision.get(
                "explicit_cloud"
            )
        )

        explicit_local = bool(
            decision.get(
                "explicit_local"
            )
        )

        cloud_authorized = bool(
            decision.get(
                "cloud_authorized"
            )
        )

        labels = {
            "local": "LOCAL",
            "cloud": "CLOUD PATH",
            "suggest_cloud": (
                "SUGGEST CLOUD"
            ),
            "block_cloud": (
                "BLOCK CLOUD"
            )
        }

        route_label = (
            labels.get(
                route,
                route.upper()
            )
        )

        reason_labels = {
            "local_default": (
                "local is the default"
            ),
            "explicit_local_request": (
                "you explicitly requested local use"
            ),
            "explicit_cloud_request": (
                "you explicitly requested cloud use"
            ),
            "cloud_may_be_helpful": (
                "cloud may be useful for this task"
            ),
            "possible_secret_or_credential": (
                "the request may contain a secret "
                "or credential"
            ),
            "possible_private_or_local_context": (
                "the request may involve private "
                "or local context"
            ),
            "empty_request": (
                "no request was provided"
            )
        }

        reason_text = (
            reason_labels.get(
                reason,
                reason
            )
        )

        authorized_text = (
            "yes"
            if cloud_authorized
            else "no"
        )

        explicit_cloud_text = (
            "yes"
            if explicit_cloud
            else "no"
        )

        explicit_local_text = (
            "yes"
            if explicit_local
            else "no"
        )

        return (
            "Aether: Route Recommendation\n\n"
            f"Request:\n{request}\n\n"
            f"Recommended route: "
            f"{route_label}\n"
            f"Reason: {reason_text}\n\n"
            f"Explicit cloud request: "
            f"{explicit_cloud_text}\n"
            f"Explicit local request: "
            f"{explicit_local_text}\n"
            f"Cloud authorized: "
            f"{authorized_text}\n\n"
            "Action taken: none\n\n"
            "The route advisor only recommends "
            "where a request belongs. "
            "It does not execute anything."
        )

    # ---------------------------------
    # LOCAL VS CLOUD ADVISOR
    # ---------------------------------

    def _show_local_cloud_advice(
        self,
        request
    ):

        if not request:

            return (
                "Aether: What request would you "
                "like me to compare?"
            )

        discovery = (
            self._discover_local_models()
        )

        installed_models = (
            discovery.get(
                "models",
                []
            )
            if discovery.get(
                "success"
            )
            else []
        )

        advice = (
            self.local_cloud_advisor
            .advise(
                request,
                installed_models
            )
        )

        recommendation = str(
            advice.get(
                "recommendation",
                "local"
            )
        ).strip()

        reason = str(
            advice.get(
                "reason",
                "unknown"
            )
        ).strip()

        local = (
            advice.get(
                "local",
                {}
            )
        )

        cloud = (
            advice.get(
                "cloud",
                {}
            )
        )

        labels = {
            "local": "LOCAL",
            "cloud": "CLOUD",
            "cloud_may_help": (
                "CLOUD MAY HELP"
            )
        }

        recommendation_label = (
            labels.get(
                recommendation,
                recommendation.upper()
            )
        )

        local_available = (
            "yes"
            if local.get(
                "available"
            )
            else "no"
        )

        local_private = (
            "yes"
            if local.get(
                "private"
            )
            else "no"
        )

        cloud_permission = (
            "yes"
            if cloud.get(
                "requires_permission"
            )
            else "no"
        )

        cloud_authorized = (
            "yes"
            if cloud.get(
                "authorized"
            )
            else "no"
        )

        discovery_text = (
            "live Ollama discovery"
            if discovery.get(
                "success"
            )
            else "Ollama discovery unavailable"
        )

        installed_text = (
            ", ".join(
                installed_models
            )
            if installed_models
            else "none detected"
        )

        return (
            "Aether: Local vs Cloud Advisor\n\n"
            f"Request:\n{request}\n\n"
            f"Recommendation: "
            f"{recommendation_label}\n"
            f"Reason: {reason}\n\n"
            "--- Local Option ---\n"
            f"Available: {local_available}\n"
            f"Model: "
            f"{local.get('model')}\n"
            f"Tier: "
            f"{local.get('tier')}\n"
            f"Private: {local_private}\n"
            "Internet required: no\n"
            f"Model source: {discovery_text}\n"
            f"Installed models: {installed_text}\n\n"
            "--- Cloud Option ---\n"
            f"Route: "
            f"{cloud.get('route')}\n"
            f"Permission required: "
            f"{cloud_permission}\n"
            f"Cloud authorized: "
            f"{cloud_authorized}\n"
            "Internet required: yes\n\n"
            "Action taken: none\n\n"
            "This comparison is advisory only."
        )

    # ---------------------------------
    # CLOUD REQUEST
    # ---------------------------------

    def _handle_cloud_request(
        self,
        request,
        evaluation
    ):

        status = (
            evaluation.get(
                "status"
            )
        )

        privacy = (
            evaluation.get(
                "privacy",
                {}
            )
        )

        reasons = (
            privacy.get(
                "reasons",
                []
            )
        )

        reason_text = (
            ", ".join(
                reasons
            )
            if reasons
            else "none"
        )

        if status == "privacy_blocked":

            return (
                "Aether: Cloud Privacy Block\n\n"
                f"Request: {request}\n\n"
                "Privacy decision: BLOCK\n"
                f"Reasons: {reason_text}\n\n"
                "Aether will not send this request "
                "to a cloud provider.\n\n"
                "Nothing was sent."
            )

        if status == "permission_required":

            return (
                "Aether: Cloud Privacy Gate\n\n"
                f"Request: {request}\n\n"
                "Privacy decision: ASK FIRST\n"
                f"Reasons: {reason_text}\n\n"
                "This request may involve local "
                "or private data.\n\n"
                "Local-data upload permission is "
                "not enabled yet.\n\n"
                "Nothing was sent."
            )

        if status != "cloud_allowed":

            return (
                "Aether: Cloud request was not "
                "approved for cloud use.\n\n"
                "Nothing was sent."
            )

        provider = (
            self._preferred_provider()
        )

        if provider is None:

            return (
                "Aether: Cloud Request\n\n"
                f"Request: {request}\n\n"
                "Privacy decision: ALLOW\n"
                f"Reasons: {reason_text}\n\n"
                "No configured cloud provider "
                "is available.\n\n"
                "Nothing was sent."
            )

        self.permissions.request(
            "cloud_request_execution",
            {
                "provider": (
                    provider.name
                ),
                "request": request,
                "capability": (
                    "cloud_generate_text"
                ),
                "privacy_decision": (
                    "allow"
                ),
                "privacy_reasons": (
                    list(
                        reasons
                    )
                )
            }
        )

        return (
            "Aether: Cloud Permission Required\n\n"
            f"Request:\n{request}\n\n"
            f"Provider: {provider.name}\n"
            "Privacy decision: ALLOW\n"
            f"Reasons: {reason_text}\n\n"
            "This prompt would leave your computer "
            "and be processed by an external cloud "
            "provider.\n\n"
            "Cloud request guard: active\n"
            "Cloud execution: enabled\n\n"
            'Say "yes" to approve or '
            '"no" to cancel.'
        )

    # ---------------------------------
    # APPROVAL
    # ---------------------------------

    def _handle_approval(
        self,
        pending
    ):

        if not isinstance(
            pending,
            dict
        ):

            return (
                "Aether: Invalid cloud permission "
                "data.\n\n"
                "Nothing was sent."
            )

        action = (
            pending.get(
                "action"
            )
        )

        data = (
            pending.get(
                "data",
                {}
            )
        )

        if action != (
            "cloud_request_execution"
        ):

            return (
                "Aether: Unknown cloud permission "
                "action.\n\n"
                "Nothing was sent."
            )

        provider_name = str(
            data.get(
                "provider",
                ""
            )
        ).strip()

        request = str(
            data.get(
                "request",
                ""
            )
        ).strip()

        capability = str(
            data.get(
                "capability",
                "cloud_generate_text"
            )
        ).strip()

        if not self.cloud_execution_enabled:

            return (
                "Aether: Cloud request approved.\n\n"
                "Cloud execution safety lock: ON\n\n"
                "Nothing was sent."
            )

        provider = (
            self.providers.get(
                provider_name
            )
        )

        if provider is None:

            return (
                "Aether: Cloud provider could "
                "not be found.\n\n"
                "Nothing was sent."
            )

        if not provider.configured():

            return (
                "Aether: Cloud provider is no "
                "longer configured.\n\n"
                "Nothing was sent."
            )

        if capability not in (
            provider.capabilities()
        ):

            return (
                "Aether: The selected cloud "
                "provider cannot perform this "
                "request.\n\n"
                "Nothing was sent."
            )

        guard = (
            self.request_guard
            .can_send()
        )

        if not guard.get(
            "allowed"
        ):

            retry_after = (
                guard.get(
                    "retry_after_seconds",
                    0
                )
            )

            return (
                "Aether: Cloud request temporarily "
                "blocked.\n\n"
                "Reason: cloud rate safety limit "
                "reached.\n\n"
                f"Limit: "
                f"{guard.get('max_requests')} "
                f"requests per "
                f"{guard.get('window_seconds')} "
                "seconds.\n"
                f"Retry after approximately "
                f"{retry_after} seconds.\n\n"
                "Nothing was sent."
            )

        # ---------------------------------
        # INTERNET BOUNDARY
        # ---------------------------------

        result = (
            provider.execute(
                capability,
                {
                    "prompt": request
                }
            )
        )

        self.last_cloud_result = (
            result
        )

        self.request_guard.record_send()

        if not isinstance(
            result,
            dict
        ):

            self.usage_tracker.record(
                provider=provider_name,
                model="unknown",
                usage={},
                success=False
            )

            return (
                "Aether: Cloud provider returned "
                "an invalid response."
            )

        success = bool(
            result.get(
                "success"
            )
        )

        model = str(
            result.get(
                "model",
                "unknown"
            )
        ).strip()

        usage = (
            result.get(
                "usage",
                {}
            )
        )

        usage_record = (
            self.usage_tracker
            .record(
                provider=provider_name,
                model=model,
                usage=usage,
                success=success
            )
        )

        if not success:

            status = (
                result.get(
                    "status",
                    "failed"
                )
            )

            error = (
                result.get(
                    "error",
                    "Unknown cloud provider error."
                )
            )

            return (
                "Aether: Cloud request failed.\n\n"
                f"Provider: {provider_name}\n"
                f"Status: {status}\n\n"
                f"{error}"
            )

        response = str(
            result.get(
                "response",
                ""
            )
        ).strip()

        if not response:

            return (
                "Aether: The cloud provider "
                "returned an empty response."
            )

        free_text = (
            "yes"
            if usage_record.get(
                "free_model"
            )
            else "no"
        )

        return (
            "Aether: Cloud Response\n\n"
            f"Provider: {provider_name}\n"
            f"Model: {model}\n"
            f"Free model: {free_text}\n\n"
            f"{response}\n\n"
            "--- Cloud Usage ---\n"
            f"Prompt tokens: "
            f"{usage_record.get('prompt_tokens')}\n"
            f"Completion tokens: "
            f"{usage_record.get('completion_tokens')}\n"
            f"Total tokens: "
            f"{usage_record.get('total_tokens')}\n"
            f"Session requests: "
            f"{self.usage_tracker.status().get('request_count')}"
        )

    # ---------------------------------
    # PREFERRED PROVIDER
    # ---------------------------------

    def _preferred_provider(
        self
    ):

        configured = (
            self.providers
            .configured()
        )

        if not configured:

            return None

        return configured[0]

    # ---------------------------------
    # STATUS
    # ---------------------------------

    def _show_status(
        self
    ):

        mode = (
            self.cloud
            .current_mode()
        )

        state = (
            "Cloud Side Mode enabled"
            if mode == "cloud"
            else "Local mode"
        )

        configured = (
            self.providers
            .configured()
        )

        configured_names = [
            provider.name
            for provider in configured
        ]

        provider_text = (
            ", ".join(
                configured_names
            )
            if configured_names
            else "none"
        )

        guard = (
            self.request_guard
            .status()
        )

        usage = (
            self.usage_tracker
            .status()
        )

        execution_state = (
            "enabled"
            if self.cloud_execution_enabled
            else "locked"
        )

        return (
            "Aether: Cloud Status\n\n"
            f"Mode: {state}\n"
            "Normal requests: local\n"
            "Cloud requests: explicit only\n"
            "Privacy gate: active\n"
            "Permission gate: active\n"
            "Request guard: active\n"
            "Usage visibility: active\n"
            "Route advisor: active\n"
            "Local vs cloud advisor: active\n"
            "Dynamic local model discovery: active\n"
            f"Cloud requests used: "
            f"{guard.get('current_requests')}/"
            f"{guard.get('max_requests')} "
            f"in {guard.get('window_seconds')} seconds\n"
            f"Session cloud requests: "
            f"{usage.get('request_count')}\n"
            f"Configured providers: {provider_text}\n"
            f"Cloud execution: {execution_state}"
        )

    # ---------------------------------
    # GUARD
    # ---------------------------------

    def _show_guard(
        self
    ):

        guard = (
            self.request_guard
            .status()
        )

        allowed = (
            "yes"
            if guard.get(
                "allowed"
            )
            else "no"
        )

        return (
            "Aether: Cloud Request Guard\n\n"
            f"Requests used: "
            f"{guard.get('current_requests')}\n"
            f"Maximum requests: "
            f"{guard.get('max_requests')}\n"
            f"Window: "
            f"{guard.get('window_seconds')} seconds\n"
            f"Cloud send currently allowed: "
            f"{allowed}\n"
            f"Retry after: "
            f"{guard.get('retry_after_seconds')} seconds"
        )

    # ---------------------------------
    # USAGE
    # ---------------------------------

    def _show_usage(
        self
    ):

        usage = (
            self.usage_tracker
            .status()
        )

        last = (
            usage.get(
                "last_request"
            )
        )

        output = (
            "Aether: Cloud Usage\n\n"
            "Session-only metadata\n"
            "Prompts/responses are not stored "
            "by this tracker.\n\n"
            f"Requests: "
            f"{usage.get('request_count')}\n"
            f"Successful: "
            f"{usage.get('success_count')}\n"
            f"Failed: "
            f"{usage.get('failure_count')}\n"
            f"Prompt tokens: "
            f"{usage.get('prompt_tokens')}\n"
            f"Completion tokens: "
            f"{usage.get('completion_tokens')}\n"
            f"Total tokens: "
            f"{usage.get('total_tokens')}"
        )

        if last is None:

            return (
                output
                + "\n\nLast request: none"
            )

        free_text = (
            "yes"
            if last.get(
                "free_model"
            )
            else "no"
        )

        return (
            output
            + "\n\nLast request:\n"
            f"Provider: "
            f"{last.get('provider')}\n"
            f"Model: "
            f"{last.get('model')}\n"
            f"Free model: {free_text}\n"
            f"Success: "
            f"{last.get('success')}"
        )

    # ---------------------------------
    # PROVIDERS
    # ---------------------------------

    def _show_providers(
        self
    ):

        providers = (
            self.providers
            .info()
        )

        if not providers:

            return (
                "Aether: No cloud providers "
                "are registered."
            )

        output = (
            "Aether: Cloud Providers\n\n"
        )

        for provider in providers:

            configured = (
                "yes"
                if provider.get(
                    "configured"
                )
                else "no"
            )

            available = (
                "yes"
                if provider.get(
                    "available"
                )
                else "no"
            )

            capabilities = (
                provider.get(
                    "capabilities",
                    []
                )
            )

            capability_text = (
                ", ".join(
                    capabilities
                )
                if capabilities
                else "none"
            )

            output += (
                f"- {provider.get('name')}\n"
                f"  Type: "
                f"{provider.get('type')}\n"
                f"  Configured: {configured}\n"
                f"  Available: {available}\n"
                f"  Capabilities: "
                f"{capability_text}\n"
                f"  Description: "
                f"{provider.get('description')}\n\n"
            )

        output += (
            "Privacy gate: active\n"
            "Permission gate: active\n"
            "Request guard: active\n"
            "Usage visibility: active\n"
            "Route advisor: active\n"
            "Local vs cloud advisor: active\n"
            "Dynamic local model discovery: active\n"
            "Cloud execution: "
            + (
                "enabled"
                if self.cloud_execution_enabled
                else "locked"
            )
        )

        return (
            output.rstrip()
        )

    # ---------------------------------
    # PENDING
    # ---------------------------------

    def has_pending_permission(
        self
    ):

        return (
            self.permissions
            .has_pending()
        )

    def cancel_pending_permission(
        self
    ):

        if not (
            self.permissions
            .has_pending()
        ):

            return False

        self.permissions.cancel()

        return True

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None