import json
import urllib.error
import urllib.request

from providers.cloud_provider import (
    CloudProvider
)

from security.secret_store import (
    SecretStore
)


class OpenRouterProvider(
    CloudProvider
):
    """
    OpenRouter cloud AI provider.

    Safety rules:
    - Credentials come from encrypted SecretStore.
    - Provider status never performs a network request.
    - Paid models are blocked by default.
    - Only explicitly free OpenRouter routes may execute.
    """

    provider_type = "cloud_ai"

    API_URL = (
        "https://openrouter.ai/api/v1/"
        "chat/completions"
    )

    DEFAULT_MODEL = (
        "openrouter/free"
    )

    REQUEST_TIMEOUT = 60

    SECRET_NAME = (
        "openrouter_api_key"
    )

    # Aether must remain free-only unless
    # we deliberately redesign this policy later.
    FREE_ONLY = True

    def __init__(
        self
    ):

        self.secrets = (
            SecretStore()
        )

    @property
    def name(
        self
    ):

        return "openrouter"

    @property
    def description(
        self
    ):

        return (
            "OpenRouter cloud AI provider "
            "with encrypted local credential storage "
            "and free-model enforcement."
        )

    # ---------------------------------
    # API KEY
    # ---------------------------------

    def api_key(
        self
    ):

        try:

            value = (
                self.secrets.get(
                    self.SECRET_NAME
                )
            )

        except Exception:

            return ""

        return str(
            value or ""
        ).strip()

    # ---------------------------------
    # CONFIGURED
    # ---------------------------------

    def configured(
        self
    ):

        try:

            return (
                self.secrets.exists(
                    self.SECRET_NAME
                )
            )

        except Exception:

            return False

    # ---------------------------------
    # AVAILABLE
    # ---------------------------------

    def available(
        self
    ):

        # Do not make a network request just
        # to determine provider status.
        return self.configured()

    # ---------------------------------
    # CAPABILITIES
    # ---------------------------------

    def capabilities(
        self
    ):

        return [
            "cloud_generate_text"
        ]

    # ---------------------------------
    # FREE MODEL CHECK
    # ---------------------------------

    def is_free_model(
        self,
        model
    ):

        model = str(
            model or ""
        ).strip().lower()

        if not model:

            return False

        if model == "openrouter/free":

            return True

        if model.endswith(
            ":free"
        ):

            return True

        return False

    # ---------------------------------
    # CREDENTIAL STATUS
    # ---------------------------------

    def credential_status(
        self
    ):

        return {
            "configured": (
                self.configured()
            ),
            "storage": (
                "windows_dpapi"
            ),
            "secret_name": (
                self.SECRET_NAME
            )
        }

    # ---------------------------------
    # SAFETY STATUS
    # ---------------------------------

    def safety_status(
        self
    ):

        return {
            "free_only": (
                self.FREE_ONLY
            ),
            "default_model": (
                self.DEFAULT_MODEL
            ),
            "paid_models_allowed": (
                not self.FREE_ONLY
            )
        }

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        capability,
        task
    ):

        if capability not in (
            self.capabilities()
        ):

            return {
                "success": False,
                "provider": self.name,
                "status": (
                    "unsupported_capability"
                ),
                "error": (
                    "Unsupported OpenRouter "
                    f'capability "{capability}".'
                )
            }

        task = (
            task
            if isinstance(
                task,
                dict
            )
            else {}
        )

        prompt = str(
            task.get(
                "prompt",
                ""
            )
        ).strip()

        model = str(
            task.get(
                "model",
                self.DEFAULT_MODEL
            )
        ).strip()

        if not prompt:

            return {
                "success": False,
                "provider": self.name,
                "status": (
                    "missing_prompt"
                ),
                "error": (
                    "No cloud prompt "
                    "was provided."
                )
            }

        # ---------------------------------
        # FREE-ONLY COST GUARD
        # ---------------------------------
        #
        # This check happens before:
        #
        # - retrieving the API key
        # - constructing the request
        # - opening a network connection
        #
        # A paid model therefore cannot reach
        # the internet while FREE_ONLY is active.

        if (
            self.FREE_ONLY
            and not self.is_free_model(
                model
            )
        ):

            return {
                "success": False,
                "provider": self.name,
                "status": (
                    "paid_model_blocked"
                ),
                "model": model,
                "sent": False,
                "error": (
                    "Aether blocked this model "
                    "because OpenRouter is currently "
                    "configured for free models only."
                )
            }

        if not self.configured():

            return {
                "success": False,
                "provider": self.name,
                "status": (
                    "not_configured"
                ),
                "error": (
                    "OpenRouter is not configured."
                )
            }

        key = (
            self.api_key()
        )

        if not key:

            return {
                "success": False,
                "provider": self.name,
                "status": (
                    "credential_unavailable"
                ),
                "error": (
                    "OpenRouter credential could "
                    "not be retrieved."
                )
            }

        payload = json.dumps(
            {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            }
        ).encode(
            "utf-8"
        )

        request = (
            urllib.request.Request(
                self.API_URL,
                data=payload,
                headers={
                    "Authorization": (
                        "Bearer "
                        + key
                    ),
                    "Content-Type": (
                        "application/json"
                    ),
                    "X-Title": (
                        "Aether"
                    )
                },
                method="POST"
            )
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=(
                    self.REQUEST_TIMEOUT
                )
            ) as response:

                data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except urllib.error.HTTPError as error:

            try:

                body = (
                    error.read()
                    .decode(
                        "utf-8",
                        errors="replace"
                    )
                )

            except Exception:

                body = ""

            return {
                "success": False,
                "provider": self.name,
                "status": (
                    "http_error"
                ),
                "http_status": (
                    error.code
                ),
                "error": (
                    body
                    or str(
                        error
                    )
                )
            }

        except (
            urllib.error.URLError,
            json.JSONDecodeError,
            TimeoutError,
            OSError
        ) as error:

            return {
                "success": False,
                "provider": self.name,
                "status": (
                    "request_failed"
                ),
                "error": str(
                    error
                )
            }

        choices = (
            data.get(
                "choices",
                []
            )
        )

        if not choices:

            return {
                "success": False,
                "provider": self.name,
                "status": (
                    "empty_response"
                ),
                "error": (
                    "OpenRouter returned "
                    "no response choices."
                )
            }

        message = (
            choices[0]
            .get(
                "message",
                {}
            )
        )

        content = (
            message.get(
                "content",
                ""
            )
        )

        return {
            "success": True,
            "provider": self.name,
            "provider_type": (
                self.provider_type
            ),
            "capability": capability,
            "model": data.get(
                "model",
                model
            ),
            "response": content,
            "usage": data.get(
                "usage",
                {}
            )
        }