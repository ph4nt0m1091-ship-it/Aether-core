from policies.cloud_privacy_policy import (
    CloudPrivacyPolicy
)


class CloudSideMode:
    """
    Controls Aether's optional cloud path.

    Important design rule:

        Local is always the default.

    Cloud access must be explicitly requested.

    Enabling cloud mode does NOT bypass the
    privacy gate.
    """

    MODE_LOCAL = "local"
    MODE_CLOUD = "cloud"

    def __init__(
        self
    ):

        self.mode = (
            self.MODE_LOCAL
        )

        self.privacy = (
            CloudPrivacyPolicy()
        )

    # ---------------------------------
    # MODE
    # ---------------------------------

    def current_mode(
        self
    ):

        return self.mode

    def is_local(
        self
    ):

        return (
            self.mode
            == self.MODE_LOCAL
        )

    def is_cloud(
        self
    ):

        return (
            self.mode
            == self.MODE_CLOUD
        )

    # ---------------------------------
    # SWITCH
    # ---------------------------------

    def use_local(
        self
    ):

        self.mode = (
            self.MODE_LOCAL
        )

        return {
            "success": True,
            "mode": (
                self.mode
            ),
            "message": (
                "Aether is using local mode."
            )
        }

    def use_cloud(
        self
    ):

        self.mode = (
            self.MODE_CLOUD
        )

        return {
            "success": True,
            "mode": (
                self.mode
            ),
            "message": (
                "Aether Cloud Side Mode "
                "is enabled."
            )
        }

    # ---------------------------------
    # EVALUATE CLOUD REQUEST
    # ---------------------------------

    def evaluate(
        self,
        text,
        metadata=None,
        explicit_cloud_request=False
    ):

        # Cloud is never silently selected.
        if (
            not self.is_cloud()
            and not explicit_cloud_request
        ):

            return {
                "success": False,
                "status": (
                    "cloud_not_requested"
                ),
                "mode": (
                    self.mode
                ),
                "cloud_allowed": False,
                "requires_permission": False,
                "reason": (
                    "Cloud was not explicitly requested."
                )
            }

        privacy = (
            self.privacy.evaluate(
                text,
                metadata=metadata
            )
        )

        decision = (
            privacy.get(
                "decision"
            )
        )

        if decision == (
            CloudPrivacyPolicy.BLOCK
        ):

            status = (
                "privacy_blocked"
            )

        elif decision == (
            CloudPrivacyPolicy.ASK
        ):

            status = (
                "permission_required"
            )

        else:

            status = (
                "cloud_allowed"
            )

        return {
            "success": (
                decision
                != CloudPrivacyPolicy.BLOCK
            ),
            "status": status,
            "mode": (
                self.mode
            ),
            "cloud_allowed": (
                privacy.get(
                    "cloud_allowed",
                    False
                )
            ),
            "requires_permission": (
                privacy.get(
                    "requires_permission",
                    False
                )
            ),
            "privacy": privacy
        }