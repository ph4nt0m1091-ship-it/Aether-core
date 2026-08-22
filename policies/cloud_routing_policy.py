class CloudRoutingPolicy:
    """
    Advisory routing intelligence for Aether.

    Important rule:

    This policy may recommend cloud usage,
    but it NEVER authorizes network execution.

    Actual cloud execution still requires:
    - an explicit cloud request
    - privacy approval
    - a configured provider
    - user permission
    - request guard approval
    - provider safety checks
    """

    ROUTE_LOCAL = "local"
    ROUTE_CLOUD = "cloud"
    ROUTE_SUGGEST_CLOUD = "suggest_cloud"
    ROUTE_BLOCK_CLOUD = "block_cloud"

    def __init__(
        self
    ):

        self.local_phrases = (
            "use local",
            "keep this local",
            "local only",
            "do this locally",
            "don't use cloud",
            "do not use cloud"
        )

        self.cloud_phrases = (
            "ask cloud",
            "ask the cloud",
            "use cloud for",
            "send to cloud"
        )

        self.secret_patterns = (
            "password",
            "api key",
            "access token",
            "refresh token",
            "private key",
            "secret key",
            "bearer token",
            "authorization header",
            "browser cookie",
            "browser cookies"
        )

        self.private_patterns = (
            "my local file",
            "local file",
            "my source code",
            "my private notes",
            "stored memory",
            "my memory",
            "my documents",
            "my document",
            "my spreadsheet",
            "my pdf",
            "my screenshot"
        )

        # These do NOT cause automatic cloud use.
        #
        # They only allow Aether to say:
        # "Cloud may be useful here."
        self.cloud_helpful_patterns = (
            "deep analysis",
            "complex reasoning",
            "very long explanation",
            "compare several approaches",
            "brainstorm many ideas",
            "second opinion",
            "another ai opinion",
            "cloud opinion"
        )

    # ---------------------------------
    # CONTAINS
    # ---------------------------------

    def _contains_any(
        self,
        text,
        patterns
    ):

        return any(
            pattern in text
            for pattern in patterns
        )

    # ---------------------------------
    # DECIDE
    # ---------------------------------

    def decide(
        self,
        message
    ):

        original = str(
            message or ""
        ).strip()

        lower = (
            original.lower()
        )

        # ---------------------------------
        # EMPTY
        # ---------------------------------

        if not original:

            return {
                "route": (
                    self.ROUTE_LOCAL
                ),
                "reason": (
                    "empty_request"
                ),
                "explicit_cloud": False,
                "explicit_local": False,
                "cloud_authorized": False
            }

        # ---------------------------------
        # SECRETS
        # ---------------------------------

        if self._contains_any(
            lower,
            self.secret_patterns
        ):

            return {
                "route": (
                    self.ROUTE_BLOCK_CLOUD
                ),
                "reason": (
                    "possible_secret_or_credential"
                ),
                "explicit_cloud": (
                    self._contains_any(
                        lower,
                        self.cloud_phrases
                    )
                ),
                "explicit_local": False,
                "cloud_authorized": False
            }

        # ---------------------------------
        # EXPLICIT LOCAL
        # ---------------------------------

        if self._contains_any(
            lower,
            self.local_phrases
        ):

            return {
                "route": (
                    self.ROUTE_LOCAL
                ),
                "reason": (
                    "explicit_local_request"
                ),
                "explicit_cloud": False,
                "explicit_local": True,
                "cloud_authorized": False
            }

        # ---------------------------------
        # PRIVATE / LOCAL CONTEXT
        # ---------------------------------

        if self._contains_any(
            lower,
            self.private_patterns
        ):

            return {
                "route": (
                    self.ROUTE_LOCAL
                ),
                "reason": (
                    "possible_private_or_local_context"
                ),
                "explicit_cloud": (
                    self._contains_any(
                        lower,
                        self.cloud_phrases
                    )
                ),
                "explicit_local": False,
                "cloud_authorized": False
            }

        # ---------------------------------
        # EXPLICIT CLOUD
        # ---------------------------------

        if self._contains_any(
            lower,
            self.cloud_phrases
        ):

            return {
                "route": (
                    self.ROUTE_CLOUD
                ),
                "reason": (
                    "explicit_cloud_request"
                ),
                "explicit_cloud": True,
                "explicit_local": False,

                # This means only that the routing
                # policy permits the request to enter
                # the existing cloud safety pipeline.
                #
                # It does NOT mean network execution
                # has been approved.
                "cloud_authorized": False
            }

        # ---------------------------------
        # CLOUD MAY HELP
        # ---------------------------------

        if self._contains_any(
            lower,
            self.cloud_helpful_patterns
        ):

            return {
                "route": (
                    self.ROUTE_SUGGEST_CLOUD
                ),
                "reason": (
                    "cloud_may_be_helpful"
                ),
                "explicit_cloud": False,
                "explicit_local": False,
                "cloud_authorized": False
            }

        # ---------------------------------
        # DEFAULT
        # ---------------------------------

        return {
            "route": (
                self.ROUTE_LOCAL
            ),
            "reason": (
                "local_default"
            ),
            "explicit_cloud": False,
            "explicit_local": False,
            "cloud_authorized": False
        }