import re

from providers.agent_router import AgentRouter

from providers.invocation_adapters.registry import (
    InvocationAdapterRegistry
)


class AgentDelegator:
    """
    Converts natural-language delegation requests
    into structured external-agent plans.

    Flow:

        natural request
        -> infer role
        -> route worker
        -> build provider-specific invocation
        -> permission/execution later
    """

    def __init__(
        self,
        project_directory=None
    ):

        self.router = AgentRouter(
            project_directory
        )

        self.adapters = (
            InvocationAdapterRegistry()
        )

    # ---------------------------------
    # BUILD PLAN
    # ---------------------------------

    def build_plan(
        self,
        request
    ):

        request = str(
            request or ""
        ).strip()

        if not request:

            return {
                "success": False,
                "status": "invalid_request",
                "error": (
                    "No delegation request "
                    "was provided."
                )
            }

        parsed = self._parse_request(
            request
        )

        if not parsed.get(
            "success"
        ):

            return parsed

        role = parsed[
            "role"
        ]

        task = parsed[
            "task"
        ]

        route = self.router.route(
            role,
            prefer_local=(
                parsed.get(
                    "prefer_local",
                    False
                )
            ),
            prefer_cloud=(
                parsed.get(
                    "prefer_cloud",
                    False
                )
            )
        )

        # ---------------------------------
        # NO INSTALLED WORKER
        # ---------------------------------

        if route.get(
            "status"
        ) == "not_installed":

            return {
                "success": False,
                "status": (
                    "worker_not_installed"
                ),
                "role": role,
                "task": task,
                "selected": None,
                "candidates": route.get(
                    "candidates",
                    []
                ),
                "error": (
                    "No installed external agent "
                    "matches this task."
                ),
                "route": route
            }

        # ---------------------------------
        # ROUTING FAILURE
        # ---------------------------------

        if route.get(
            "status"
        ) != "selected":

            return {
                "success": False,
                "status": route.get(
                    "status",
                    "routing_failed"
                ),
                "role": role,
                "task": task,
                "selected": None,
                "candidates": route.get(
                    "candidates",
                    []
                ),
                "error": route.get(
                    "error",
                    "Agent routing failed."
                ),
                "route": route
            }

        selected = route.get(
            "selected",
            {}
        )

        provider_name = (
            selected.get(
                "name"
            )
        )

        # ---------------------------------
        # BUILD INVOCATION
        # ---------------------------------

        invocation = (
            self.adapters.build(
                provider_name=(
                    provider_name
                ),
                task=task,
                role=role
            )
        )

        if not invocation.get(
            "success"
        ):

            return {
                "success": False,
                "status": (
                    "invocation_unavailable"
                ),
                "role": role,
                "task": task,
                "selected": selected,
                "provider": (
                    provider_name
                ),
                "invocation": invocation,
                "error": invocation.get(
                    "error",
                    (
                        "The worker was selected, "
                        "but its invocation could "
                        "not be built."
                    )
                ),
                "route": route
            }

        return {
            "success": True,
            "status": (
                "invocation_built"
            ),
            "role": role,
            "task": task,
            "selected": selected,
            "provider": (
                provider_name
            ),
            "requires_permission": (
                invocation.get(
                    "requires_permission",
                    True
                )
            ),
            "execution_ready": (
                invocation.get(
                    "execution_ready",
                    False
                )
            ),
            "invocation": invocation,
            "route": route
        }

    # ---------------------------------
    # PARSE REQUEST
    # ---------------------------------

    def _parse_request(
        self,
        request
    ):

        lower = (
            request.lower()
        )

        first = re.match(
            (
                r"^ask\s+(?:an?\s+)?"
                r"(.+?)\s+agent\s+to\s+(.+)$"
            ),
            request,
            re.IGNORECASE
        )

        role_text = None
        task = None

        if first:

            role_text = (
                first.group(1)
                .strip()
            )

            task = (
                first.group(2)
                .strip()
            )

        else:

            second = re.match(
                (
                    r"^delegate\s+(.+?)\s+to\s+"
                    r"(?:an?\s+)?(.+?)\s+agent$"
                ),
                request,
                re.IGNORECASE
            )

            if second:

                task = (
                    second.group(1)
                    .strip()
                )

                role_text = (
                    second.group(2)
                    .strip()
                )

        if not role_text or not task:

            return {
                "success": False,
                "status": "not_delegation",
                "error": (
                    "The request was not recognized "
                    "as an agent delegation."
                )
            }

        role = self._infer_role(
            role_text,
            task
        )

        return {
            "success": True,
            "role": role,
            "task": task,
            "prefer_local": (
                "local" in lower
            ),
            "prefer_cloud": (
                "cloud" in lower
            )
        }

    # ---------------------------------
    # INFER ROLE
    # ---------------------------------

    def _infer_role(
        self,
        role_text,
        task
    ):

        text = (
            str(
                role_text
            )
            + " "
            + str(
                task
            )
        ).lower()

        if (
            "review" in text
            and any(
                value in text
                for value in (
                    "code",
                    ".py",
                    ".js",
                    ".ts",
                    ".java",
                    ".cpp"
                )
            )
        ):

            return "code_review"

        if any(
            phrase in text
            for phrase in (
                "debug",
                "fix bug",
                "fix bugs",
                "fix this error"
            )
        ):

            return "debugging"

        if any(
            word in text
            for word in (
                "coding",
                "coder",
                "code",
                "programming",
                "developer"
            )
        ):

            return "coding"

        if any(
            word in text
            for word in (
                "research",
                "researcher",
                "investigate"
            )
        ):

            return "research"

        if any(
            word in text
            for word in (
                "automation",
                "automate"
            )
        ):

            return "automation"

        if "git" in text:

            return "git"

        return self.router.normalize_role(
            role_text
        )