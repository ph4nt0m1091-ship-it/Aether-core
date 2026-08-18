import json
import urllib.error
import urllib.request

from providers.base_provider import BaseProvider


class OllamaProvider(BaseProvider):
    """
    Connects Aether to a local Ollama server.

    Capabilities:
    - list_models
    - generate_text
    """

    name = "ollama"

    description = (
        "Local AI model provider powered by Ollama."
    )

    BASE_URL = (
        "http://127.0.0.1:11434"
    )

    def available(self):

        try:

            request = urllib.request.Request(
                self.BASE_URL
                + "/api/tags",
                method="GET"
            )

            with urllib.request.urlopen(
                request,
                timeout=2
            ) as response:

                return (
                    response.status
                    == 200
                )

        except (
            urllib.error.URLError,
            TimeoutError,
            OSError
        ):

            return False

    def capabilities(self):

        return [
            "list_models",
            "generate_text"
        ]

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(
        self,
        capability,
        task
    ):

        if capability == "list_models":

            return self._list_models()

        if capability == "generate_text":

            return self._generate_text(
                task
            )

        return {
            "success": False,
            "provider": self.name,
            "error": (
                f'Unsupported capability: '
                f'"{capability}"'
            )
        }

    # ---------------------------------
    # LIST MODELS
    # ---------------------------------

    def _list_models(self):

        try:

            request = urllib.request.Request(
                self.BASE_URL
                + "/api/tags",
                method="GET"
            )

            with urllib.request.urlopen(
                request,
                timeout=5
            ) as response:

                data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except (
            urllib.error.URLError,
            json.JSONDecodeError,
            TimeoutError,
            OSError
        ) as error:

            return {
                "success": False,
                "provider": self.name,
                "error": str(
                    error
                )
            }

        models = []

        for item in data.get(
            "models",
            []
        ):

            name = item.get(
                "name"
            )

            if name:

                models.append(
                    name
                )

        return {
            "success": True,
            "provider": self.name,
            "capability": "list_models",
            "models": models
        }

    # ---------------------------------
    # GENERATE TEXT
    # ---------------------------------

    def _generate_text(
        self,
        task
    ):

        if not isinstance(
            task,
            dict
        ):

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "Ollama task must be "
                    "a dictionary."
                )
            }

        model = task.get(
            "model",
            ""
        ).strip()

        prompt = task.get(
            "prompt",
            ""
        ).strip()

        if not model:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "No Ollama model was provided."
                )
            }

        if not prompt:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "No prompt was provided."
                )
            }

        payload = json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        ).encode(
            "utf-8"
        )

        request = urllib.request.Request(
            self.BASE_URL
            + "/api/generate",
            data=payload,
            headers={
                "Content-Type": (
                    "application/json"
                )
            },
            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=120
            ) as response:

                data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except (
            urllib.error.URLError,
            json.JSONDecodeError,
            TimeoutError,
            OSError
        ) as error:

            return {
                "success": False,
                "provider": self.name,
                "error": str(
                    error
                )
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "generate_text",
            "model": model,
            "response": data.get(
                "response",
                ""
            )
        }
