from permissions.permission_manager import (
    PermissionManager
)

from policies.cloud_side_mode import (
    CloudSideMode
)

from providers.cloud_provider_registry import (
    CloudProviderRegistry
)


class CloudSideModeSkill:
    """
    Controls Aether's optional Cloud Side Mode.

    Cloud Permission Bridge v1:

    - Local remains the default.
    - Cloud must be explicitly requested.
    - Privacy policy runs before provider routing.
    - Provider must be configured.
    - Explicit Aether permission is required.
    - Actual network execution remains locked.

    Nothing is sent to a cloud provider in v1.
    """

    name = "cloud_side_mode"

    description = (
        "Controls Aether's optional privacy-gated "
        "and permission-gated cloud side mode."
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

        self.permissions = (
            PermissionManager()
        )

        self.last_evaluation = None

        self.last_cloud_result = None

        # ---------------------------------
        # NETWORK EXECUTION SAFETY LOCK
        # ---------------------------------

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
        # PENDING CLOUD PERMISSION
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
                "Cloud is only used when explicitly "
                "requested.\n\n"
                "Privacy gate: active\n"
                "Permission gate: active\n"
                "Cloud execution: locked"
            )

        # ---------------------------------
        # RETURN TO LOCAL
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

                matched_prefix = prefix
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
    # HANDLE CLOUD REQUEST
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
        # BLOCK
        # ---------------------------------

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

        # ---------------------------------
        # LOCAL DATA NEEDS DIFFERENT
        # PERMISSION FLOW LATER
        # ---------------------------------

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

        # ---------------------------------
        # PROVIDER
        # ---------------------------------

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

        # ---------------------------------
        # REQUEST PERMISSION
        # ---------------------------------

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
            "Cloud execution safety lock: ON\n\n"
            'Say "yes" to approve or '
            '"no" to cancel.'
        )

    # ---------------------------------
    # HANDLE APPROVAL
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

        provider_name = (
            data.get(
                "provider",
                "unknown"
            )
        )

        request = (
            data.get(
                "request",
                ""
            )
        )

        # ---------------------------------
        # SAFETY LOCK
        # ---------------------------------
        #
        # Permission behavior is being
        # proven before network execution
        # is enabled.

        result = {
            "success": False,
            "status": (
                "approved_but_locked"
            ),
            "provider": (
                provider_name
            ),
            "request": request,
            "approved": True,
            "sent": False,
            "execution_enabled": (
                self.cloud_execution_enabled
            ),
            "reason": (
                "Cloud permission was approved, "
                "but network execution remains "
                "safety-locked."
            )
        }

        self.last_cloud_result = (
            result
        )

        return (
            "Aether: Cloud request approved.\n\n"
            f"Provider: {provider_name}\n"
            f"Request: {request}\n\n"
            "Cloud execution safety lock: ON\n\n"
            "The permission bridge worked, but "
            "network execution is still disabled "
            "for this safety test.\n\n"
            "Nothing was sent."
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
            f"Configured providers: {provider_text}\n"
            f"Cloud execution: {execution_state}"
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