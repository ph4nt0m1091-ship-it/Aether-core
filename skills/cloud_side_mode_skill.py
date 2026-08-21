from policies.cloud_side_mode import (
    CloudSideMode
)

from providers.cloud_provider_registry import (
    CloudProviderRegistry
)


class CloudSideModeSkill:
    """
    Controls Aether's optional Cloud Side Mode.

    Cloud Provider Integration v1:

    - Local remains the default.
    - Cloud must be explicitly requested.
    - Privacy policy runs first.
    - Cloud provider registry runs second.
    - Provider configuration is visible.
    - Actual cloud execution remains locked.

    Nothing is sent to a cloud provider in v1.
    """

    name = "cloud_side_mode"

    description = (
        "Controls Aether's optional privacy-gated "
        "cloud side mode and cloud providers."
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

        self.last_evaluation = None

        self.last_cloud_result = None

        # ---------------------------------
        # SAFETY LOCK
        # ---------------------------------
        #
        # Provider integration is being
        # tested before network execution
        # is enabled.

        self.cloud_execution_enabled = False

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
        # CLOUD STATUS
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
        # CLOUD PROVIDERS
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
                "Cloud is only used when you explicitly "
                'say something like "ask cloud ...".\n\n'
                "Privacy gate: active\n"
                "Cloud execution: locked"
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
                "Cloud Side Mode is off.\n"
                "Normal requests remain local."
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

        # ---------------------------------
        # PRIVACY BLOCK
        # ---------------------------------

        if status == "privacy_blocked":

            return (
                "Aether: Cloud Privacy Block\n\n"
                f"Request: {request}\n\n"
                "Privacy decision: BLOCK\n"
                f"Reasons: {reason_text}\n\n"
                "Aether will not send this request "
                "to any cloud provider.\n\n"
                "Nothing was sent."
            )

        # ---------------------------------
        # PERMISSION REQUIRED
        # ---------------------------------

        if status == "permission_required":

            return (
                "Aether: Cloud Privacy Gate\n\n"
                f"Request: {request}\n\n"
                "Privacy decision: ASK FIRST\n"
                f"Reasons: {reason_text}\n\n"
                "This request may involve local "
                "or private information.\n\n"
                "Aether requires explicit permission "
                "before local data may leave this "
                "computer.\n\n"
                "Nothing was sent."
            )

        # ---------------------------------
        # NOT ALLOWED FOR OTHER REASON
        # ---------------------------------

        if status != "cloud_allowed":

            return (
                "Aether: Cloud request was not "
                "approved for cloud use.\n\n"
                "Nothing was sent."
            )

        # ---------------------------------
        # PRIVACY ALLOWED
        # ---------------------------------
        #
        # Now — and only now — inspect
        # cloud provider availability.

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
                "is currently available.\n\n"
                "Nothing was sent."
            )

        # ---------------------------------
        # EXECUTION SAFETY LOCK
        # ---------------------------------

        if not self.cloud_execution_enabled:

            return (
                "Aether: Cloud Request Ready\n\n"
                f"Request: {request}\n\n"
                "Privacy decision: ALLOW\n"
                f"Reasons: {reason_text}\n"
                f"Provider: {provider.name}\n"
                "Provider configured: "
                f"{provider.configured()}\n\n"
                "Cloud execution safety lock: ON\n\n"
                "The privacy gate and provider "
                "routing succeeded, but network "
                "execution is still disabled.\n\n"
                "Nothing was sent."
            )

        # ---------------------------------
        # FUTURE EXECUTION PATH
        # ---------------------------------
        #
        # Intentionally unreachable while
        # cloud_execution_enabled is False.

        return (
            "Aether: Cloud execution is not "
            "enabled in this version."
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

        # v1 uses the first configured
        # provider.
        #
        # Later this becomes CloudRouter.

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

        if mode == "cloud":

            state = (
                "Cloud Side Mode enabled"
            )

        else:

            state = (
                "Local mode"
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
            f"Configured providers: {provider_text}\n"
            f"Cloud execution: {execution_state}"
        )

    # ---------------------------------
    # SHOW PROVIDERS
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
            "Cloud execution safety lock: "
            + (
                "OFF"
                if self.cloud_execution_enabled
                else "ON"
            )
        )

        return (
            output.rstrip()
        )

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        step
    ):

        return None