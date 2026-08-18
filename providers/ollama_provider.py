import json
import urllib.error
import urllib.request

from providers.base_provider import BaseProvider


class OllamaProvider(BaseProvider):
    """
    Fast local Ollama provider for Aether.

    Optimizations:
    - Direct localhost API connection
    - Keeps models loaded between requests
    - Disables thinking by default for quick tasks
    - Limits context/output for lower-memory systems
    - Supports model warm-up
    """

    name = "ollama"

    description = (
        "Local AI model provider powered by Ollama."
    )

    BASE_URL = "http://127.0.0.1:11434"

    DEFAULT_KEEP_ALIVE = "30m"

    DEFAULT_CONTEXT = 2048

    DEFAULT_MAX_OUTPUT = 160

    REQUEST_TIMEOUT = 300

    # ---------------------------------
    # AVAILABLE
    # ---------------------------------

    def available(self):

        try:

            request = urllib.request.Request(
                self.BASE_URL + "/api/tags",
                method="GET"
            )

            with urllib.request.urlopen(
                request,
                timeout=2
            ) as response:

                return response.status == 200

        except (
            urllib.error.URLError,
            TimeoutError,
            OSError
        ):

            return False

    # ---------------------------------
    # CAPABILITIES
    # ---------------------------------

    def capabilities(self):

        return [
            "list_models",
            "generate_text",
            "warm_model"
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

        if capability == "warm_model":

            return self._warm_model(
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
                self.BASE_URL + "/api/tags",
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
                "error": str(error)
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
    # WARM MODEL
    # ---------------------------------

    def _warm_model(
        self,
        task
    ):

        if isinstance(
            task,
            dict
        ):

            model = task.get(
                "model",
                ""
            ).strip()

        else:

            model = str(
                task
            ).strip()

        if not model:

            return {
                "success": False,
                "provider": self.name,
                "error": (
                    "No Ollama model was provided."
                )
            }

        payload = json.dumps(
            {
                "model": model,
                "prompt": "",
                "stream": False,
                "keep_alive": (
                    self.DEFAULT_KEEP_ALIVE
                )
            }
        ).encode(
            "utf-8"
        )

        request = urllib.request.Request(
            self.BASE_URL + "/api/generate",
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=self.REQUEST_TIMEOUT
            ) as response:

                json.loads(
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
                "error": str(error)
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "warm_model",
            "model": model,
            "status": "loaded"
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

        keep_alive = task.get(
            "keep_alive",
            self.DEFAULT_KEEP_ALIVE
        )

        context_size = task.get(
            "num_ctx",
            self.DEFAULT_CONTEXT
        )

        max_output = task.get(
            "num_predict",
            self.DEFAULT_MAX_OUTPUT
        )

        think = task.get(
            "think",
            False
        )

        payload = json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "think": think,
                "keep_alive": keep_alive,
                "options": {
                    "num_ctx": context_size,
                    "num_predict": max_output
                }
            }
        ).encode(
            "utf-8"
        )

        request = urllib.request.Request(
            self.BASE_URL + "/api/generate",
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=self.REQUEST_TIMEOUT
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
                "error": str(error)
            }

        return {
            "success": True,
            "provider": self.name,
            "capability": "generate_text",
            "model": model,
            "response": data.get(
                "response",
                ""
            ),
            "load_duration": data.get(
                "load_duration",
                0
            ),
            "total_duration": data.get(
                "total_duration",
                0
            ),
            "eval_count": data.get(
                "eval_count",
                0
            ),
            "eval_duration": data.get(
                "eval_duration",
                0
            )
        }