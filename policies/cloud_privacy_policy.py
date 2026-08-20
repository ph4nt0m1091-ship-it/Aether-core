import re


class CloudPrivacyPolicy:
    """
    Privacy gate for Aether's optional cloud path.

    Cloud is never assumed to be safe simply because
    the user enabled or requested it.

    Decisions:

        allow
            Safe enough for ordinary cloud use.

        ask
            Local/private context may leave the machine.
            Explicit confirmation is required.

        block
            Highly sensitive credential-like information
            must not be sent to cloud providers.
    """

    ALLOW = "allow"
    ASK = "ask"
    BLOCK = "block"

    # ---------------------------------
    # HIGH-RISK / BLOCKED DATA
    # ---------------------------------

    BLOCK_PATTERNS = [
        (
            "password",
            re.compile(
                r"\bpassword\b",
                re.IGNORECASE
            )
        ),
        (
            "api_key",
            re.compile(
                r"\bapi[\s_-]*key\b",
                re.IGNORECASE
            )
        ),
        (
            "access_token",
            re.compile(
                r"\baccess[\s_-]*token\b",
                re.IGNORECASE
            )
        ),
        (
            "refresh_token",
            re.compile(
                r"\brefresh[\s_-]*token\b",
                re.IGNORECASE
            )
        ),
        (
            "secret_key",
            re.compile(
                r"\bsecret[\s_-]*key\b",
                re.IGNORECASE
            )
        ),
        (
            "private_key",
            re.compile(
                r"\bprivate[\s_-]*key\b",
                re.IGNORECASE
            )
        ),
        (
            "browser_cookie",
            re.compile(
                r"\b(?:browser\s+)?cookies?\b",
                re.IGNORECASE
            )
        ),
        (
            "authorization_header",
            re.compile(
                r"\bauthorization\s*:",
                re.IGNORECASE
            )
        ),
        (
            "bearer_token",
            re.compile(
                r"\bbearer\s+[A-Za-z0-9._~+/=-]+",
                re.IGNORECASE
            )
        )
    ]

    # ---------------------------------
    # LOCAL CONTEXT / ASK FIRST
    # ---------------------------------

    ASK_PATTERNS = [
        (
            "local_file",
            re.compile(
                r"\b(?:my|this|local)\s+file\b",
                re.IGNORECASE
            )
        ),
        (
            "project_file",
            re.compile(
                r"\b(?:brain|main|memory|config)"
                r"\.(?:py|json|yaml|yml|txt)\b",
                re.IGNORECASE
            )
        ),
        (
            "source_code",
            re.compile(
                r"\b(?:my|this|local)\s+"
                r"(?:code|source code|project code)\b",
                re.IGNORECASE
            )
        ),
        (
            "stored_memory",
            re.compile(
                r"\b(?:my|stored|saved)\s+memory\b",
                re.IGNORECASE
            )
        ),
        (
            "private_notes",
            re.compile(
                r"\b(?:my|private|personal)\s+notes?\b",
                re.IGNORECASE
            )
        ),
        (
            "local_document",
            re.compile(
                r"\b(?:my|this|local)\s+"
                r"(?:document|pdf|spreadsheet)\b",
                re.IGNORECASE
            )
        ),
        (
            "screenshot",
            re.compile(
                r"\b(?:my|this|local)\s+screenshot\b",
                re.IGNORECASE
            )
        )
    ]

    # ---------------------------------
    # EVALUATE
    # ---------------------------------

    def evaluate(
        self,
        text,
        metadata=None
    ):

        text = str(
            text or ""
        )

        metadata = (
            metadata
            if isinstance(
                metadata,
                dict
            )
            else {}
        )

        reasons = []

        # ---------------------------------
        # EXPLICIT METADATA BLOCKS
        # ---------------------------------

        if metadata.get(
            "contains_credentials",
            False
        ):

            return self._decision(
                self.BLOCK,
                [
                    "credential_data"
                ]
            )

        if metadata.get(
            "contains_secrets",
            False
        ):

            return self._decision(
                self.BLOCK,
                [
                    "secret_data"
                ]
            )

        # ---------------------------------
        # TEXT BLOCK RULES
        # ---------------------------------

        for name, pattern in (
            self.BLOCK_PATTERNS
        ):

            if pattern.search(
                text
            ):

                reasons.append(
                    name
                )

        if reasons:

            return self._decision(
                self.BLOCK,
                reasons
            )

        # ---------------------------------
        # EXPLICIT LOCAL DATA
        # ---------------------------------

        ask_reasons = []

        metadata_checks = {
            "contains_local_file": (
                "local_file"
            ),
            "contains_project_code": (
                "project_code"
            ),
            "contains_memory": (
                "stored_memory"
            ),
            "contains_document": (
                "local_document"
            ),
            "contains_image": (
                "local_image"
            )
        }

        for key, reason in (
            metadata_checks.items()
        ):

            if metadata.get(
                key,
                False
            ):

                ask_reasons.append(
                    reason
                )

        # ---------------------------------
        # TEXT ASK RULES
        # ---------------------------------

        for name, pattern in (
            self.ASK_PATTERNS
        ):

            if pattern.search(
                text
            ):

                ask_reasons.append(
                    name
                )

        if ask_reasons:

            return self._decision(
                self.ASK,
                sorted(
                    set(
                        ask_reasons
                    )
                )
            )

        # ---------------------------------
        # NORMAL CLOUD-SAFE REQUEST
        # ---------------------------------

        return self._decision(
            self.ALLOW,
            [
                "no_sensitive_local_context_detected"
            ]
        )

    # ---------------------------------
    # DECISION
    # ---------------------------------

    def _decision(
        self,
        decision,
        reasons
    ):

        requires_permission = (
            decision == self.ASK
        )

        cloud_allowed = (
            decision
            in (
                self.ALLOW,
                self.ASK
            )
        )

        return {
            "decision": decision,
            "cloud_allowed": (
                cloud_allowed
            ),
            "requires_permission": (
                requires_permission
            ),
            "reasons": list(
                reasons
            )
        }