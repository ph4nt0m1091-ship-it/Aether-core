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

    Credentials are retrieved from Aether's
    encrypted SecretStore.

    Privacy approval must happen before this
    provider is called.
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
            "with encrypted local credential storage."
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
                "error": (
                    "Unsupported OpenRouter "
                    f'capability "{capability}".'
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
                "error": (
                    "No cloud prompt "
                    "was provided."
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