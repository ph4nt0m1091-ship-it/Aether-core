import re

from providers.browser_provider import BrowserProvider


class BrowserPermissionState:
    """
    Small permission state used by BrowserSkill.

    The interface intentionally matches what Aether's
    workflow bridge expects:
    - has_pending()
    - cancel()
    """

    def __init__(self):
        self.pending = None

    def has_pending(self):
        return self.pending is not None

    def request(
        self,
        action,
        data,
    ):
        self.pending = {
            "action": action,
            "data": data,
        }

    def peek(self):
        return self.pending

    def take(self):
        pending = self.pending
        self.pending = None
        return pending

    def cancel(self):
        self.pending = None


class BrowserSkill:
    """
    Safe local browser control.

    Uses Playwright DOM targeting instead of
    blind screen coordinates.
    """

    name = "browser"

    description = (
        "Controls a local Chromium browser using exact "
        "DOM/accessibility targets with permission-gated "
        "fill and click actions."
    )

    def __init__(
        self,
        memory,
    ):
        self.memory = memory

        self.provider = BrowserProvider()

        self.permissions = (
            BrowserPermissionState()
        )

        self.last_execution_result = None

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message,
    ):
        message = message.strip()

        lower = message.lower()

        # ---------------------------------
        # ACTIVE PERMISSION
        # ---------------------------------

        if self.permissions.has_pending():

            if lower in (
                "no",
                "n",
                "cancel",
                "deny",
            ):
                self.permissions.cancel()

                self.last_execution_result = {
                    "success": False,
                    "cancelled": True,
                    "response": (
                        "Aether: Browser action cancelled."
                    ),
                }

                return (
                    "Aether: Browser action cancelled."
                )

            if lower not in (
                "yes",
                "y",
                "approve",
                "allow",
            ):
                return (
                    "Aether: A browser permission request "
                    "is waiting.\n"
                    'Say "yes" to approve or "no" to cancel.'
                )

            pending = self.permissions.take()

            data = dict(
                pending.get(
                    "data",
                    {},
                )
            )

            data[
                "permission_granted"
            ] = True

            result = self.provider.execute(
                pending.get(
                    "action"
                ),
                data,
            )

            self.last_execution_result = (
                result
            )

            return self._format_result(
                result
            )

        # ---------------------------------
        # NAVIGATE
        # ---------------------------------

        navigate_patterns = (
            r"^browser\s+open\s+(.+)$",
            r"^browse\s+to\s+(.+)$",
            r"^go\s+to\s+(https?://\S+|\S+\.\S+)$",
        )

        for pattern in navigate_patterns:

            match = re.match(
                pattern,
                message,
                re.IGNORECASE,
            )

            if match:
                url = (
                    match.group(1)
                    .strip()
                    .strip('"')
                )

                result = self.provider.execute(
                    "browser_navigate",
                    {
                        "url": url,
                    },
                )

                self.last_execution_result = (
                    result
                )

                return self._format_result(
                    result
                )

        # ---------------------------------
        # INSPECT
        # ---------------------------------

        if lower in (
            "show page elements",
            "list page elements",
            "show browser elements",
            "list browser elements",
            "inspect page",
            "inspect browser page",
        ):
            result = self.provider.execute(
                "browser_inspect",
                {},
            )

            self.last_execution_result = (
                result
            )

            return self._format_elements(
                result
            )

        # ---------------------------------
        # FILL
        # ---------------------------------

        fill_match = re.match(
            r'^fill\s+"([^"]+)"\s+with\s+(.+)$',
            message,
            re.IGNORECASE,
        )

        if fill_match:

            field = (
                fill_match.group(1)
                .strip()
            )

            text = (
                fill_match.group(2)
                .strip()
            )

            if (
                len(text) >= 2
                and text[0] == '"'
                and text[-1] == '"'
            ):
                text = text[1:-1]

            self.permissions.request(
                "browser_fill",
                {
                    "field": field,
                    "text": text,
                },
            )

            return (
                "Aether: Permission required.\n\n"
                f'Fill browser field: {field}\n'
                f"Characters: {len(text)}\n\n"
                "Aether will type into exactly one matching "
                "visible field. It will not submit the form, "
                "and password fields are blocked.\n\n"
                'Say "yes" to approve or "no" to cancel.'
            )

        # ---------------------------------
        # CLICK
        # ---------------------------------

        click_match = re.match(
            r'^browser\s+click\s+"([^"]+)"$',
            message,
            re.IGNORECASE,
        )

        if click_match:

            target = (
                click_match.group(1)
                .strip()
            )

            self.permissions.request(
                "browser_click",
                {
                    "target": target,
                },
            )

            return (
                "Aether: Permission required.\n\n"
                f"Browser element: {target}\n\n"
                "Aether will click exactly one matching "
                "enabled visible DOM element. "
                "No screen coordinates will be used.\n\n"
                'Say "yes" to approve or "no" to cancel.'
            )

        # ---------------------------------
        # STATUS
        # ---------------------------------

        if lower in (
            "browser status",
            "show browser status",
        ):

            result = self.provider.execute(
                "browser_status",
                {},
            )

            self.last_execution_result = (
                result
            )

            return self._format_result(
                result
            )

        # ---------------------------------
        # CLOSE
        # ---------------------------------

        if lower in (
            "close browser session",
            "end browser session",
        ):

            result = self.provider.execute(
                "browser_close",
                {},
            )

            self.last_execution_result = (
                result
            )

            return self._format_result(
                result
            )

        return None

    # ---------------------------------
    # FORMAT RESULT
    # ---------------------------------

    def _format_result(
        self,
        result,
    ):
        if not isinstance(
            result,
            dict,
        ):
            return (
                "Aether: Browser returned an "
                "invalid result."
            )

        if not result.get(
            "success",
            False,
        ):
            return (
                "Aether: Browser action failed.\n"
                + result.get(
                    "error",
                    "Unknown browser error.",
                )
            )

        response = str(
            result.get(
                "response",
                "",
            )
            or ""
        ).strip()

        if response:
            if response.startswith(
                "Aether:"
            ):
                return response

            return (
                "Aether: "
                + response
            )

        return (
            "Aether: Browser action completed."
        )

    def _format_elements(
        self,
        result,
    ):
        if not result.get(
            "success",
            False,
        ):
            return self._format_result(
                result
            )

        elements = result.get(
            "elements",
            [],
        )

        output = (
            "Aether: Browser Page Elements\n\n"
        )

        if not elements:
            output += (
                "No supported visible elements found."
            )

            return output

        for item in elements[:60]:

            label = item.get(
                "label",
                "(unnamed)",
            )

            tag = item.get(
                "tag",
                "",
            )

            item_type = item.get(
                "type",
                "",
            )

            details = tag

            if item_type:
                details += (
                    f":{item_type}"
                )

            output += (
                f"- {label} | {details}\n"
            )

        if len(elements) > 60:
            output += (
                f"\nShowing 60 of "
                f"{len(elements)} elements."
            )

        return output.rstrip()

    # ---------------------------------
    # STRUCTURED EXECUTE
    # ---------------------------------

    def execute(
        self,
        step,
    ):
        return None
