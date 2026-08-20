import re

from providers.agent_router import AgentRouter


class AgentDelegator:
    """
    Converts natural-language delegation requests
    into structured external-agent plans.

    This layer does NOT execute an agent.

    Execution is handled later by the selected
    agent's invocation adapter and Aether's
    permission system.
    """

    def __init__(
        self,
        project_directory=None
    ):

        self.router = AgentRouter(
            project_directory
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

        role = parsed["role"]
        task = parsed["task"]

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
        # WORKER SELECTED
        # ---------------------------------

        if route.get(
            "status"
        ) == "selected":

            selected = route.get(
                "selected",
                {}
            )

            return {
                "success": True,
                "status": "planned",
                "role": role,
                "task": task,
                "selected": selected,
                "provider": selected.get(
                    "name"
                ),
                "requires_permission": (
                    selected.get(
                        "requires_permission",
                        True
                    )
                ),
                "execution_ready": False,
                "reason": (
                    "A suitable installed worker "
                    "was selected. An invocation "
                    "adapter is still required "
                    "before natural-language task "
                    "execution."
                ),
                "route": route
            }

        # ---------------------------------
        # KNOWN BUT NOT INSTALLED
        # ---------------------------------

        if route.get(
            "status"
        ) == "not_installed":

            return {
                "success": False,
                "status": "worker_not_installed",
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
        # CAPABILITY GAP
        # ---------------------------------

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

    # ---------------------------------
    # PARSE REQUEST
    # ---------------------------------

    def _parse_request(
        self,
        request
    ):

        lower = request.lower()

        patterns = [
            r"^ask\s+(?:an?\s+)?(.+?)\s+agent\s+to\s+(.+)$",
            r"^delegate\s+(.+?)\s+to\s+(?:an?\s+)?(.+?)\s+agent$"
        ]

        role_text = None
        task = None

        first = re.match(
            patterns[0],
            request,
            re.IGNORECASE
        )

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
                patterns[1],
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
            str(role_text)
            + " "
            + str(task)
        ).lower()

        # Review must come before general coding.
        if any(
            phrase in text
            for phrase in (
                "review code",
                "review my code",
                "code review",
                "review brain.py",
                "review this file"
            )
        ) or (
            "review" in text
            and any(
                word in text
                for word in (
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