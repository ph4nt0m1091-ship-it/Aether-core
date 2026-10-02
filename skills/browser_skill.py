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
    # NATURAL BROWSER GOAL PLANNING
    # ---------------------------------

    def _resolve_goal_site(
        self,
        site,
    ):
        site = str(
            site or ""
        ).strip().strip('"')

        lower = site.lower()

        aliases = {
            "wikipedia": (
                "https://www.wikipedia.org"
            ),
            "wikipedia.org": (
                "https://www.wikipedia.org"
            ),
            "www.wikipedia.org": (
                "https://www.wikipedia.org"
            ),
        }

        if lower in aliases:
            return aliases[lower]

        if lower.startswith(
            (
                "http://",
                "https://",
            )
        ):
            return site

        if (
            "." in site
            and " " not in site
        ):
            return (
                "https://"
                + site
            )

        return None

    def _goal_field_candidate(
        self,
        elements,
    ):
        candidates = []

        for item in elements:

            tag = str(
                item.get(
                    "tag",
                    "",
                )
            ).lower()

            field_type = str(
                item.get(
                    "type",
                    "",
                )
            ).lower()

            label = str(
                item.get(
                    "label",
                    "",
                )
            ).strip()

            lower_label = (
                label.lower()
            )

            if tag not in (
                "input",
                "textarea",
            ):
                continue

            score = 0

            if field_type == "search":
                score += 100

            if lower_label == "search":
                score += 80

            elif "search" in lower_label:
                score += 40

            elif (
                "query" in lower_label
                or "find" in lower_label
            ):
                score += 20

            if score > 0:

                candidates.append(
                    (
                        score,
                        label,
                    )
                )

        if not candidates:
            return (
                None,
                "No clear search field was found "
                "on the live page."
            )

        best_score = max(
            item[0]
            for item in candidates
        )

        best = [
            item
            for item in candidates
            if item[0] == best_score
        ]

        labels = {
            item[1]
            for item in best
        }

        if len(best) != 1:

            return (
                None,
                "The page has multiple equally likely "
                "search fields. I will not guess."
            )

        label = best[0][1]

        if not label:

            return (
                None,
                "The search field does not expose a safe "
                "exact name that Aether can target."
            )

        return (
            label,
            None,
        )

    def _goal_button_candidate(
        self,
        elements,
    ):
        candidates = []

        for item in elements:

            tag = str(
                item.get(
                    "tag",
                    "",
                )
            ).lower()

            item_type = str(
                item.get(
                    "type",
                    "",
                )
            ).lower()

            label = str(
                item.get(
                    "label",
                    "",
                )
            ).strip()

            lower_label = (
                label.lower()
            )

            if tag not in (
                "button",
                "input",
                "a",
            ):
                continue

            score = 0

            if lower_label == "search":
                score += 100

            elif "search" in lower_label:
                score += 50

            if item_type == "submit":
                score += 60

            if score > 0:

                candidates.append(
                    (
                        score,
                        label,
                    )
                )

        if not candidates:
            return (
                None,
                "No clear search action was found "
                "on the live page."
            )

        best_score = max(
            item[0]
            for item in candidates
        )

        best = [
            item
            for item in candidates
            if item[0] == best_score
        ]

        if len(best) != 1:

            return (
                None,
                "The page has multiple equally likely "
                "search actions. I will not guess."
            )

        label = best[0][1]

        if not label:

            return (
                None,
                "The search action does not expose a safe "
                "exact name that Aether can target."
            )

        return (
            label,
            None,
        )

    def plan_natural_search_goal(
        self,
        message,
    ):
        """
        Convert a narrow natural browser-search goal into
        an exact workflow using live page evidence.

        Returns None when the message is not a supported
        natural browser goal.
        """

        message = str(
            message or ""
        ).strip()

        match = re.match(
            r'^(?:go to|visit|open)\s+'
            r'(.+?)\s+and\s+'
            r'(?:search(?:\s+for)?|look up)\s+'
            r'(.+)$',
            message,
            re.IGNORECASE,
        )

        if match is None:
            return None

        site = (
            match.group(1)
            .strip()
            .strip('"')
        )

        query = (
            match.group(2)
            .strip()
        )

        if (
            len(query) >= 2
            and query[0] == '"'
            and query[-1] == '"'
        ):
            query = query[1:-1]

        query = query.strip()

        if not query:

            return {
                "success": False,
                "response": (
                    "Aether: Browser goal planning stopped.\n"
                    "No search text was provided."
                ),
            }

        if len(query) > 500:

            return {
                "success": False,
                "response": (
                    "Aether: Browser goal planning stopped.\n"
                    "The search text is too long for "
                    "Browser Goal Planning v1."
                ),
            }

        if (
            "\n" in query
            or "\r" in query
            or "\t" in query
        ):

            return {
                "success": False,
                "response": (
                    "Aether: Browser goal planning stopped.\n"
                    "Control characters are not allowed "
                    "in this browser goal."
                ),
            }

        # WorkflowSkill currently separates natural steps
        # using the literal phrase " then ".
        if " then " in query.lower():

            return {
                "success": False,
                "response": (
                    "Aether: Browser goal planning stopped.\n"
                    'The search text contains the reserved '
                    'workflow separator "then".'
                ),
            }

        url = self._resolve_goal_site(
            site
        )

        if url is None:

            return {
                "success": False,
                "response": (
                    "Aether: Browser Goal Planning v1 "
                    "doesn't recognize that site safely.\n"
                    "Use an explicit domain/URL, or the "
                    "supported site alias Wikipedia."
                ),
            }

        # Navigation and inspection are read-only / low-risk.
        navigation = (
            self.provider.execute(
                "browser_navigate",
                {
                    "url": url,
                },
            )
        )

        self.last_execution_result = (
            navigation
        )

        if not navigation.get(
            "success",
            False,
        ):

            return {
                "success": False,
                "response": (
                    self._format_result(
                        navigation
                    )
                ),
            }

        inspection = (
            self.provider.execute(
                "browser_inspect",
                {},
            )
        )

        if not inspection.get(
            "success",
            False,
        ):

            return {
                "success": False,
                "response": (
                    self._format_result(
                        inspection
                    )
                ),
            }

        elements = inspection.get(
            "elements",
            [],
        )

        field, field_error = (
            self._goal_field_candidate(
                elements
            )
        )

        if field_error:

            return {
                "success": False,
                "response": (
                    "Aether: Browser goal planning stopped.\n"
                    + field_error
                ),
            }

        target, target_error = (
            self._goal_button_candidate(
                elements
            )
        )

        if target_error:

            return {
                "success": False,
                "response": (
                    "Aether: Browser goal planning stopped.\n"
                    + target_error
                ),
            }

        # Exact-match workflow syntax cannot safely contain
        # quote characters in the chosen element names.
        if (
            '"' in field
            or '"' in target
        ):

            return {
                "success": False,
                "response": (
                    "Aether: Browser goal planning stopped.\n"
                    "A required page element contains an "
                    "unsupported quote character."
                ),
            }

        workflow_request = (
            f'fill "{field}" with {query}'
            f' then browser click "{target}"'
        )

        return {
            "success": True,
            "site": site,
            "url": navigation.get(
                "url",
                url,
            ),
            "title": navigation.get(
                "title",
                "",
            ),
            "query": query,
            "field": field,
            "target": target,
            "workflow_request": (
                workflow_request
            ),
        }

    # ---------------------------------
    # BROWSER GOAL PLANNING V2
    # ---------------------------------

    def _normalize_goal_label(
        self,
        value,
    ):
        value = str(
            value or ""
        ).strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            " ",
            value,
        )

        return " ".join(
            value.split()
        )

    def _goal_named_element_candidate(
        self,
        elements,
        requested_target,
    ):
        requested = (
            self._normalize_goal_label(
                requested_target
            )
        )

        if not requested:
            return (
                None,
                "No browser element name was provided."
            )

        # Natural phrases like "pricing page" should still
        # be able to match a live element named "Pricing".
        simplified = requested

        removable_suffixes = (
            " page",
            " link",
            " button",
        )

        for suffix in removable_suffixes:

            if simplified.endswith(
                suffix
            ):
                simplified = (
                    simplified[
                        :-len(suffix)
                    ].strip()
                )

        candidates = []

        for item in elements:

            tag = str(
                item.get(
                    "tag",
                    "",
                )
            ).lower()

            if tag not in (
                "a",
                "button",
                "input",
            ):
                continue

            label = str(
                item.get(
                    "label",
                    "",
                )
            ).strip()

            if not label:
                continue

            normalized = (
                self._normalize_goal_label(
                    label
                )
            )

            if normalized == requested:

                candidates.append(
                    (
                        300,
                        label,
                    )
                )

                continue

            if (
                simplified
                and normalized
                == simplified
            ):

                candidates.append(
                    (
                        250,
                        label,
                    )
                )

                continue

            if (
                simplified
                and simplified
                in normalized
            ):

                candidates.append(
                    (
                        100,
                        label,
                    )
                )

        if not candidates:

            return (
                None,
                (
                    "No visible clickable element matched "
                    f'"{requested_target}".'
                )
            )

        best_score = max(
            item[0]
            for item in candidates
        )

        best = [
            item
            for item in candidates
            if item[0] == best_score
        ]

        unique_labels = []

        for _, label in best:

            if label not in unique_labels:
                unique_labels.append(
                    label
                )

        if len(unique_labels) != 1:

            return (
                None,
                (
                    "Multiple live page elements matched "
                    f'"{requested_target}". '
                    "I will not guess."
                )
            )

        return (
            unique_labels[0],
            None,
        )

    def _goal_named_field_candidate(
        self,
        elements,
        requested_field,
    ):
        requested = (
            self._normalize_goal_label(
                requested_field
            )
        )

        if not requested:

            return (
                None,
                "No field name was provided."
            )

        exact = []

        partial = []

        for item in elements:

            tag = str(
                item.get(
                    "tag",
                    "",
                )
            ).lower()

            if tag not in (
                "input",
                "textarea",
            ):
                continue

            item_type = str(
                item.get(
                    "type",
                    "",
                )
            ).lower()

            if item_type == "password":

                continue

            label = str(
                item.get(
                    "label",
                    "",
                )
            ).strip()

            if not label:
                continue

            normalized = (
                self._normalize_goal_label(
                    label
                )
            )

            if normalized == requested:

                exact.append(
                    label
                )

            elif requested in normalized:

                partial.append(
                    label
                )

        candidates = (
            exact
            if exact
            else partial
        )

        unique = []

        for label in candidates:

            if label not in unique:
                unique.append(
                    label
                )

        if not unique:

            return (
                None,
                (
                    "No visible editable field matched "
                    f'"{requested_field}".'
                )
            )

        if len(unique) != 1:

            return (
                None,
                (
                    "Multiple live fields matched "
                    f'"{requested_field}". '
                    "I will not guess."
                )
            )

        return (
            unique[0],
            None,
        )

    def _prepare_goal_page(
        self,
        site,
    ):
        url = self._resolve_goal_site(
            site
        )

        if url is None:

            return {
                "success": False,
                "response": (
                    "Aether: Browser Goal Planning v2 "
                    "doesn't recognize that site safely.\n"
                    "Use an explicit domain/URL or a "
                    "supported site alias."
                ),
            }

        navigation = (
            self.provider.execute(
                "browser_navigate",
                {
                    "url": url,
                },
            )
        )

        self.last_execution_result = (
            navigation
        )

        if not navigation.get(
            "success",
            False,
        ):

            return {
                "success": False,
                "response": (
                    self._format_result(
                        navigation
                    )
                ),
            }

        inspection = (
            self.provider.execute(
                "browser_inspect",
                {},
            )
        )

        if not inspection.get(
            "success",
            False,
        ):

            return {
                "success": False,
                "response": (
                    self._format_result(
                        inspection
                    )
                ),
            }

        return {
            "success": True,
            "url": navigation.get(
                "url",
                url,
            ),
            "title": navigation.get(
                "title",
                "",
            ),
            "elements": inspection.get(
                "elements",
                [],
            ),
        }

    def _plan_click_continuation_goal(
        self,
        message,
    ):
        """
        Plan one verified click followed by observation of
        the page that exists after the click.
        """

        message = str(
            message or ""
        ).strip()

        match = re.match(
            r'^(?:go to|visit|open)\s+'
            r'(.+?)'
            r'(?:,\s*|\s+and\s+)'
            r'click\s+'
            r'(.+?)'
            r'(?:,\s*|\s+)'
            r'then\s+'
            r'(.+)$',
            message,
            re.IGNORECASE,
        )

        if match is None:
            return None

        site = (
            match.group(1)
            .strip()
            .strip('"')
        )

        requested_target = (
            match.group(2)
            .strip()
            .strip('"')
        )

        continuation = (
            match.group(3)
            .strip()
            .lower()
            .rstrip(".")
        )

        status_requests = (
            "tell me what page it opened",
            "tell me what page opened",
            "show me what page it opened",
            "show me what page opened",
            "tell me where it went",
            "show me where it went",
        )

        inspect_requests = (
            "inspect the page",
            "inspect page",
            "show page elements",
            "show me the page elements",
        )

        if (
            continuation not in status_requests
            and continuation not in inspect_requests
        ):
            return None

        page = self._prepare_goal_page(
            site
        )

        if not page.get(
            "success",
            False,
        ):
            return page

        target, error = (
            self._goal_named_element_candidate(
                page["elements"],
                requested_target,
            )
        )

        if error:

            return {
                "success": False,
                "response": (
                    "Aether: Browser goal planning "
                    "stopped.\n"
                    + error
                ),
            }

        if '"' in target:

            return {
                "success": False,
                "response": (
                    "Aether: Browser goal planning stopped.\n"
                    "The target contains an unsupported "
                    "quote character."
                ),
            }

        if continuation in inspect_requests:

            workflow_request = (
                f'browser click "{target}"'
                f' then inspect page'
            )

        else:

            workflow_request = (
                f'browser click "{target}"'
                f' then inspect page'
                f' then browser status'
            )

        return {
            "success": True,
            "site": site,
            "url": page["url"],
            "title": page["title"],
            "field": None,
            "target": target,
            "continuation": True,
            "workflow_request": (
                workflow_request
            ),
        }

    def plan_natural_browser_goal(
        self,
        message,
    ):
        """
        Browser Goal Planning v2.

        Search goals continue through the existing v1
        deterministic planner.

        Additional supported goals:
        - go to SITE and click TARGET
        - go to SITE and find TARGET
        - go to SITE and fill FIELD with TEXT

        Every target is checked against the live DOM before
        a workflow is created.
        """

        continuation_goal = (
            self._plan_click_continuation_goal(
                message
            )
        )

        if continuation_goal is not None:
            return continuation_goal

        existing_search = (
            self.plan_natural_search_goal(
                message
            )
        )

        if existing_search is not None:
            return existing_search

        message = str(
            message or ""
        ).strip()

        # ---------------------------------
        # FILL GOAL
        # ---------------------------------

        fill_match = re.match(
            r'^(?:go to|visit|open)\s+'
            r'(.+?)\s+and\s+'
            r'fill\s+"([^"]+)"\s+with\s+'
            r'(.+)$',
            message,
            re.IGNORECASE,
        )

        if fill_match:

            site = (
                fill_match.group(1)
                .strip()
                .strip('"')
            )

            requested_field = (
                fill_match.group(2)
                .strip()
            )

            value = (
                fill_match.group(3)
                .strip()
            )

            if (
                len(value) >= 2
                and value[0] == '"'
                and value[-1] == '"'
            ):
                value = value[1:-1]

            if not value:

                return {
                    "success": False,
                    "response": (
                        "Aether: Browser goal planning "
                        "stopped. No text was provided."
                    ),
                }

            if len(value) > 500:

                return {
                    "success": False,
                    "response": (
                        "Aether: Browser goal planning "
                        "stopped. The text is too long."
                    ),
                }

            if any(
                char in value
                for char in (
                    "\n",
                    "\r",
                    "\t",
                )
            ):

                return {
                    "success": False,
                    "response": (
                        "Aether: Browser goal planning "
                        "stopped. Control characters "
                        "are not allowed."
                    ),
                }

            if " then " in value.lower():

                return {
                    "success": False,
                    "response": (
                        "Aether: Browser goal planning "
                        "stopped. The text contains the "
                        'reserved workflow separator "then".'
                    ),
                }

            page = (
                self._prepare_goal_page(
                    site
                )
            )

            if not page.get(
                "success",
                False,
            ):
                return page

            field, error = (
                self._goal_named_field_candidate(
                    page["elements"],
                    requested_field,
                )
            )

            if error:

                return {
                    "success": False,
                    "response": (
                        "Aether: Browser goal planning "
                        "stopped.\n"
                        + error
                    ),
                }

            if '"' in field:

                return {
                    "success": False,
                    "response": (
                        "Aether: Browser goal planning "
                        "stopped. The field name contains "
                        "an unsupported quote character."
                    ),
                }

            return {
                "success": True,
                "site": site,
                "url": page["url"],
                "title": page["title"],
                "field": field,
                "target": None,
                "workflow_request": (
                    f'fill "{field}" with {value}'
                ),
            }

        # ---------------------------------
        # CLICK / FIND GOAL
        # ---------------------------------

        click_match = re.match(
            r'^(?:go to|visit|open)\s+'
            r'(.+?)\s+and\s+'
            r'(?:click|find|open)\s+'
            r'(.+)$',
            message,
            re.IGNORECASE,
        )

        if click_match:

            site = (
                click_match.group(1)
                .strip()
                .strip('"')
            )

            requested_target = (
                click_match.group(2)
                .strip()
                .strip('"')
            )

            if not requested_target:

                return {
                    "success": False,
                    "response": (
                        "Aether: Browser goal planning "
                        "stopped. No target was provided."
                    ),
                }

            page = (
                self._prepare_goal_page(
                    site
                )
            )

            if not page.get(
                "success",
                False,
            ):
                return page

            target, error = (
                self._goal_named_element_candidate(
                    page["elements"],
                    requested_target,
                )
            )

            if error:

                return {
                    "success": False,
                    "response": (
                        "Aether: Browser goal planning "
                        "stopped.\n"
                        + error
                    ),
                }

            if '"' in target:

                return {
                    "success": False,
                    "response": (
                        "Aether: Browser goal planning "
                        "stopped. The target contains an "
                        "unsupported quote character."
                    ),
                }

            return {
                "success": True,
                "site": site,
                "url": page["url"],
                "title": page["title"],
                "field": None,
                "target": target,
                "workflow_request": (
                    f'browser click "{target}"'
                ),
            }

        return None

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
