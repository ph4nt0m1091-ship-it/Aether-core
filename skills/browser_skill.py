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

        # Foreground-only browser goal agent state.
        # This is intentionally not persisted across restarts.
        self.agent_goal = None
        self.agent_max_hops = 3

        # Visible non-navigation page text used only for
        # deterministic goal verification.
        self.agent_content_char_limit = 8000

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

    # ---------------------------------
    # BROWSER GOAL AGENT V4
    # ---------------------------------

    def _agent_goal_tokens(
        self,
        value,
    ):
        normalized = (
            self._normalize_goal_label(
                value
            )
        )

        stop_words = {
            "a",
            "an",
            "and",
            "about",
            "find",
            "for",
            "in",
            "of",
            "on",
            "page",
            "reach",
            "the",
            "to",
            "that",
            "explains",
            "explaining",
        }

        return [
            token
            for token in normalized.split()
            if (
                len(token) >= 2
                and token not in stop_words
            )
        ]

    def _agent_concept_groups(
        self,
    ):
        """
        Small deterministic synonym families.

        These are intentionally curated instead of asking
        a language model whether two words are related.
        """

        return (
            {
                "pricing",
                "price",
                "prices",
                "plan",
                "plans",
                "cost",
                "costs",
                "fee",
                "fees",
                "subscription",
                "subscriptions",
            },
            {
                "support",
                "help",
                "assistance",
                "service",
            },
            {
                "contact",
                "contacts",
                "reach",
                "email",
            },
            {
                "docs",
                "doc",
                "documentation",
                "guide",
                "guides",
                "manual",
                "manuals",
                "reference",
            },
            {
                "download",
                "downloads",
                "installer",
                "install",
                "setup",
            },
            {
                "feature",
                "features",
                "capability",
                "capabilities",
            },
            {
                "security",
                "secure",
                "safety",
            },
            {
                "privacy",
                "private",
            },
            {
                "job",
                "jobs",
                "career",
                "careers",
                "employment",
            },
            {
                "login",
                "signin",
                "sign",
                "account",
            },
        )

    def _agent_token_variants(
        self,
        token,
    ):
        token = (
            self._normalize_goal_label(
                token
            )
        )

        if not token:
            return set()

        variants = {
            token,
        }

        # ---------------------------------
        # SIMPLE SINGULAR / PLURAL SUPPORT
        # ---------------------------------

        if (
            token.endswith("ies")
            and len(token) > 4
        ):

            variants.add(
                token[:-3]
                + "y"
            )

        elif (
            token.endswith("s")
            and len(token) > 3
        ):

            variants.add(
                token[:-1]
            )

        else:

            variants.add(
                token
                + "s"
            )

        # ---------------------------------
        # CURATED CONCEPT GROUPS
        # ---------------------------------

        for group in (
            self._agent_concept_groups()
        ):

            if variants & group:

                variants.update(
                    group
                )

        return variants

    def _agent_match_goal_tokens(
        self,
        goal,
        candidate_tokens,
    ):
        """
        Match each goal concept against candidate words.

        Returns:
        - matched count
        - total concept count
        - human-readable matched pairs
        """

        goal_tokens = (
            self._agent_goal_tokens(
                goal
            )
        )

        candidate_tokens = set(
            candidate_tokens
        )

        matched = []

        for goal_token in goal_tokens:

            variants = (
                self._agent_token_variants(
                    goal_token
                )
            )

            exact = (
                goal_token
                in candidate_tokens
            )

            synonym_matches = (
                variants
                & candidate_tokens
            )

            if exact:

                matched.append(
                    (
                        goal_token,
                        goal_token,
                        "exact",
                    )
                )

                continue

            if synonym_matches:

                chosen = sorted(
                    synonym_matches
                )[0]

                matched.append(
                    (
                        goal_token,
                        chosen,
                        "related",
                    )
                )

        return (
            matched,
            len(goal_tokens),
        )

    def _agent_page_key(
        self,
        title,
        url,
        visible_text,
    ):
        """
        Deterministic fingerprint for loop detection.

        URL + title + the beginning of non-navigation
        content prevents ordinary same-URL page changes
        from automatically looking identical.
        """

        normalized_title = (
            self._normalize_goal_label(
                title
            )
        )

        normalized_content = (
            self._normalize_goal_label(
                visible_text
            )
        )

        normalized_url = str(
            url or ""
        ).split(
            "#",
            1,
        )[0].rstrip("/").lower()

        return (
            normalized_url
            + "|"
            + normalized_title
            + "|"
            + normalized_content[:500]
        )

    def _agent_visible_page_text(
        self,
    ):
        """
        Read visible page content for goal verification.

        Navigation and interactive controls are removed first
        so a link named after the goal does not by itself prove
        that the current page satisfies the goal.
        """

        try:

            page = (
                self.provider
                ._ensure_page()
            )

            content = page.evaluate(
                """() => {
                    const source =
                        document.querySelector('main')
                        || document.querySelector('article')
                        || document.body;

                    if (!source) {
                        return '';
                    }

                    const clone =
                        source.cloneNode(true);

                    const remove =
                        'script, style, noscript, '
                        + 'nav, header, footer, '
                        + 'a, button, input, '
                        + 'textarea, select, option, '
                        + '[role="button"], '
                        + '[role="link"]';

                    clone
                        .querySelectorAll(remove)
                        .forEach(
                            element => element.remove()
                        );

                    return (
                        clone.textContent || ''
                    )
                    .replace(/\s+/g, ' ')
                    .trim();
                }"""
            )

        except Exception:
            return ""

        content = str(
            content or ""
        ).strip()

        return content[
            :self.agent_content_char_limit
        ]

    def _agent_snapshot(
        self,
    ):
        status = self.provider.execute(
            "browser_status",
            {},
        )

        if not status.get(
            "success",
            False,
        ):
            return {
                "success": False,
                "response": self._format_result(
                    status
                ),
            }

        inspection = self.provider.execute(
            "browser_inspect",
            {},
        )

        if not inspection.get(
            "success",
            False,
        ):
            return {
                "success": False,
                "response": self._format_result(
                    inspection
                ),
            }

        return {
            "success": True,
            "title": status.get(
                "title",
                "",
            ),
            "url": status.get(
                "url",
                "",
            ),
            "elements": inspection.get(
                "elements",
                [],
            ),
            "visible_text": (
                self._agent_visible_page_text()
            ),
        }

    def _agent_goal_evidence(
        self,
        goal,
        title,
        url,
        visible_text,
    ):
        """
        Deterministically verify whether the current page
        satisfies the goal.

        Strong evidence can come from:
        - title / URL
        - exact phrase in page content
        - all goal concepts appearing close together in
          visible non-navigation content

        Synonyms come only from Aether's curated groups.
        """

        goal_tokens = (
            self._agent_goal_tokens(
                goal
            )
        )

        if not goal_tokens:

            return {
                "complete": False,
            }

        # ---------------------------------
        # TITLE / URL
        # ---------------------------------

        title_url_text = (
            self._normalize_goal_label(
                (
                    str(title or "")
                    + " "
                    + str(url or "")
                )
            )
        )

        title_url_tokens = (
            title_url_text.split()
        )

        matched, total = (
            self._agent_match_goal_tokens(
                goal,
                title_url_tokens,
            )
        )

        if (
            total > 0
            and len(matched) == total
        ):

            return {
                "complete": True,
                "source": (
                    "page title or URL"
                ),
                "excerpt": (
                    str(title or "")
                    or str(url or "")
                ),
                "matched": matched,
            }

        # ---------------------------------
        # PAGE-FINDING GOALS
        # ---------------------------------
        #
        # Browser Agent currently starts from requests such as:
        #
        #   find the page about X
        #
        # For that kind of goal, body text is useful evidence
        # for choosing the next link, but a teaser/section that
        # merely mentions X must not prove that this is the
        # destination page.
        #
        # Completion therefore requires page-identity evidence
        # from the title or URL. Content-aware answering will
        # use a separate goal type later.
        # ---------------------------------

        return {
            "complete": False,
        }

        # ---------------------------------
        # VISIBLE PAGE CONTENT
        # ---------------------------------

        normalized_content = (
            self._normalize_goal_label(
                visible_text
            )
        )

        content_tokens = (
            normalized_content.split()
        )

        normalized_goal = (
            self._normalize_goal_label(
                goal
            )
        )

        # Strongest content signal:
        # the literal normalized phrase exists.
        if (
            normalized_goal
            and normalized_goal
            in normalized_content
        ):

            return {
                "complete": True,
                "source": (
                    "visible page content"
                ),
                "excerpt": (
                    self._agent_content_excerpt(
                        visible_text,
                        goal_tokens,
                    )
                ),
                "matched": [
                    (
                        token,
                        token,
                        "exact",
                    )
                    for token in goal_tokens
                ],
            }

        # Related concepts must occur reasonably close
        # together instead of merely somewhere within
        # the entire 8,000-character page snapshot.
        window_size = 60

        if len(
            content_tokens
        ) <= window_size:

            windows = [
                content_tokens
            ]

        else:

            windows = []

            step = 20

            for start in range(
                0,
                len(content_tokens),
                step,
            ):

                window = (
                    content_tokens[
                        start:
                        start + window_size
                    ]
                )

                if not window:
                    break

                windows.append(
                    window
                )

        for window in windows:

            matched, total = (
                self._agent_match_goal_tokens(
                    goal,
                    window,
                )
            )

            if (
                total > 0
                and len(matched) == total
            ):

                return {
                    "complete": True,
                    "source": (
                        "related concepts in visible "
                        "page content"
                    ),
                    "excerpt": (
                        self._agent_content_excerpt(
                            visible_text,
                            goal_tokens,
                        )
                    ),
                    "matched": matched,
                }

        return {
            "complete": False,
        }

    def _agent_content_excerpt(
        self,
        visible_text,
        goal_tokens,
    ):
        raw = str(
            visible_text or ""
        ).strip()

        if not raw:
            return ""

        lower = raw.lower()

        positions = []

        for token in goal_tokens:

            variants = (
                self._agent_token_variants(
                    token
                )
            )

            for variant in variants:

                position = lower.find(
                    variant.lower()
                )

                if position >= 0:
                    positions.append(
                        position
                    )

        if positions:

            position = min(
                positions
            )

        else:

            position = 0

        start = max(
            0,
            position - 80,
        )

        end = min(
            len(raw),
            position + 300,
        )

        return (
            raw[
                start:end
            ]
            .strip()
        )

    def _agent_choose_target(
        self,
        elements,
        goal,
        url,
    ):
        goal_tokens = (
            self._agent_goal_tokens(
                goal
            )
        )

        if not goal_tokens:

            return (
                None,
                None,
                "The browser goal does not contain "
                "enough specific words to plan safely."
            )

        state = (
            self.agent_goal
            or {}
        )

        used_pairs = {
            (
                str(
                    item.get(
                        "url",
                        "",
                    )
                ),
                str(
                    item.get(
                        "target",
                        "",
                    )
                ),
            )
            for item in state.get(
                "history",
                [],
            )
            if isinstance(
                item,
                dict,
            )
        }

        candidates = []

        normalized_goal = (
            self._normalize_goal_label(
                goal
            )
        )

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

            if (
                str(url or ""),
                label,
            ) in used_pairs:
                continue

            normalized_label = (
                self._normalize_goal_label(
                    label
                )
            )

            label_tokens = (
                normalized_label.split()
            )

            matched, total = (
                self._agent_match_goal_tokens(
                    goal,
                    label_tokens,
                )
            )

            score = 0

            reasons = []

            # Exact whole-goal phrase is strongest.
            if (
                normalized_goal
                and normalized_goal
                == normalized_label
            ):

                score += 600

                reasons.append(
                    "exact goal phrase"
                )

            elif (
                normalized_goal
                and normalized_goal
                in normalized_label
            ):

                score += 350

                reasons.append(
                    "goal phrase appears in label"
                )

            # Individual concept matches.
            for (
                goal_word,
                matched_word,
                match_type,
            ) in matched:

                if match_type == "exact":

                    score += 140

                else:

                    score += 95

                if (
                    goal_word
                    == matched_word
                ):

                    reasons.append(
                        goal_word
                    )

                else:

                    reasons.append(
                        (
                            goal_word
                            + "?"
                            + matched_word
                        )
                    )

            # Reward complete concept coverage.
            if (
                total > 0
                and len(matched) == total
            ):

                score += 250

                reasons.append(
                    "all goal concepts matched"
                )

            candidates.append(
                {
                    "label": label,
                    "score": score,
                    "matched": matched,
                    "reason_parts": reasons,
                }
            )

        if not candidates:

            return (
                None,
                None,
                "No unused visible clickable elements "
                "are available for the goal."
            )

        matching = [
            item
            for item in candidates
            if item[
                "score"
            ] > 0
        ]

        if matching:

            best_score = max(
                item[
                    "score"
                ]
                for item in matching
            )

            best = [
                item
                for item in matching
                if item[
                    "score"
                ] == best_score
            ]

            unique = []

            for item in best:

                if (
                    item["label"]
                    not in unique
                ):

                    unique.append(
                        item[
                            "label"
                        ]
                    )

            if len(unique) != 1:

                tied = ", ".join(
                    unique[:5]
                )

                return (
                    None,
                    None,
                    (
                        "Multiple live page elements "
                        "have the same best relevance score "
                        f"({best_score}): {tied}. "
                        "I will not guess."
                    ),
                )

            winner = best[0]

            reason_parts = (
                winner.get(
                    "reason_parts",
                    [],
                )
            )

            if reason_parts:

                reason = (
                    "matched "
                    + ", ".join(
                        reason_parts
                    )
                    + f" (score {best_score})"
                )

            else:

                reason = (
                    "best deterministic relevance "
                    f"score ({best_score})"
                )

            return (
                winner[
                    "label"
                ],
                reason,
                None,
            )

        # ---------------------------------
        # SAFE EXPLORATION
        # ---------------------------------
        #
        # If there is exactly one possible clickable
        # element, preserve v4's bounded exploration.
        # If there is more than one unexplained choice,
        # stop instead of guessing.
        # ---------------------------------

        unique = []

        for item in candidates:

            if (
                item["label"]
                not in unique
            ):

                unique.append(
                    item[
                        "label"
                    ]
                )

        if len(unique) == 1:

            return (
                unique[0],
                (
                    "it is the only unused visible "
                    "clickable option"
                ),
                None,
            )

        return (
            None,
            None,
            (
                "No live element has a strong enough "
                "deterministic relationship to the goal, "
                "and multiple exploratory choices exist. "
                "I will not guess."
            ),
        )

    def _agent_permission_message(
        self,
        target,
        reason,
        title,
        url,
    ):
        state = self.agent_goal or {}

        next_hop = (
            int(
                state.get(
                    "hops",
                    0,
                )
            )
            + 1
        )

        return (
            "Aether: Browser goal agent\n"
            f"Goal: {state.get('goal', '')}\n"
            f"Page: {title or url}\n"
            f"Verified next action: {target}\n"
            f"Reason: {reason}\n"
            f"Hop: {next_hop} of "
            f"{state.get('max_hops', self.agent_max_hops)}\n\n"
            "Aether: Permission required.\n\n"
            f"Browser element: {target}\n\n"
            "Aether will click exactly one matching "
            "enabled visible DOM element. "
            "No screen coordinates will be used.\n\n"
            'Say "yes" to approve or "no" to cancel.'
        )

    def _agent_continue_from_snapshot(
        self,
        snapshot,
    ):
        state = self.agent_goal

        if state is None:

            return (
                "Aether: Browser goal agent is not active."
            )

        if not snapshot.get(
            "success",
            False,
        ):
            self.agent_goal = None

            return snapshot.get(
                "response",
                (
                    "Aether: Browser goal agent stopped "
                    "because the page could not be inspected."
                ),
            )

        title = snapshot.get(
            "title",
            "",
        )

        url = snapshot.get(
            "url",
            "",
        )

        visible_text = snapshot.get(
            "visible_text",
            "",
        )

        # ---------------------------------
        # LOOP DETECTION
        # ---------------------------------

        page_key = (
            self._agent_page_key(
                title,
                url,
                visible_text,
            )
        )

        visited_pages = (
            state.setdefault(
                "visited_pages",
                [],
            )
        )

        if (
            page_key in visited_pages
            and state.get(
                "hops",
                0,
            ) > 0
        ):

            goal = state.get(
                "goal",
                "",
            )

            self.agent_goal = None

            return (
                "Aether: Browser goal agent stopped safely.\n"
                f"Goal: {goal}\n"
                "Reason: the browser returned to a page "
                "state that Aether already inspected. "
                "Continuing could create a loop.\n"
                f"Title: {title}\n"
                f"URL: {url}"
            )

        if page_key not in visited_pages:

            visited_pages.append(
                page_key
            )

        evidence = (
            self._agent_goal_evidence(
                state.get(
                    "goal",
                    "",
                ),
                title,
                url,
                snapshot.get(
                    "visible_text",
                    "",
                ),
            )
        )

        if evidence.get(
            "complete",
            False,
        ):
            hops = state.get(
                "hops",
                0,
            )

            goal = state.get(
                "goal",
                "",
            )

            source = evidence.get(
                "source",
                "verified page evidence",
            )

            excerpt = str(
                evidence.get(
                    "excerpt",
                    "",
                )
                or ""
            ).strip()

            if len(excerpt) > 300:
                excerpt = (
                    excerpt[:297]
                    .rstrip()
                    + "..."
                )

            self.agent_goal = None

            output = (
                "Aether: Browser goal completed.\n"
                f"Goal: {goal}\n"
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Verified by: {source}\n"
                f"Approved clicks used: {hops}"
            )

            matched = evidence.get(
                "matched",
                [],
            )

            if matched:

                match_text = []

                for (
                    goal_word,
                    matched_word,
                    match_type,
                ) in matched:

                    if (
                        goal_word
                        == matched_word
                    ):

                        match_text.append(
                            goal_word
                        )

                    else:

                        match_text.append(
                            (
                                goal_word
                                + "?"
                                + matched_word
                            )
                        )

                if match_text:

                    output += (
                        "\nMatched concepts: "
                        + ", ".join(
                            match_text
                        )
                    )

            if excerpt:

                output += (
                    "\nEvidence: "
                    + excerpt
                )

            return output

        if (
            state.get(
                "hops",
                0,
            )
            >= state.get(
                "max_hops",
                self.agent_max_hops,
            )
        ):
            goal = state.get(
                "goal",
                "",
            )

            self.agent_goal = None

            return (
                "Aether: Browser goal agent stopped safely.\n"
                f"Goal: {goal}\n"
                "The maximum approved-click limit "
                "was reached before the goal was verified.\n"
                f"Title: {title}\n"
                f"URL: {url}"
            )

        target, reason, error = (
            self._agent_choose_target(
                snapshot.get(
                    "elements",
                    [],
                ),
                state.get(
                    "goal",
                    "",
                ),
                url,
            )
        )

        if error:
            goal = state.get(
                "goal",
                "",
            )

            self.agent_goal = None

            return (
                "Aether: Browser goal agent stopped safely.\n"
                f"Goal: {goal}\n"
                + error
                + "\n"
                f"Title: {title}\n"
                f"URL: {url}"
            )

        state.setdefault(
            "history",
            [],
        ).append(
            {
                "url": url,
                "target": target,
            }
        )

        self.permissions.request(
            "browser_click",
            {
                "target": target,
                "_agent_goal": True,
            },
        )

        return self._agent_permission_message(
            target,
            reason,
            title,
            url,
        )

    def _continue_browser_agent(
        self,
    ):
        return self._agent_continue_from_snapshot(
            self._agent_snapshot()
        )

    def start_goal_driven_navigation(
        self,
        message,
    ):
        """
        Start a bounded foreground browser agent.

        Supported v4 shape:
        go to SITE and find the page about GOAL
        """

        message = str(
            message or ""
        ).strip()

        match = re.match(
            r'^(?:go to|visit|open)\s+'
            r'(.+?)\s+and\s+'
            r'find\s+(?:the\s+|a\s+)?page\s+'
            r'(?:about|explaining|that\s+explains)\s+'
            r'(.+)$',
            message,
            re.IGNORECASE,
        )

        if match is None:
            return None

        if self.permissions.has_pending():

            return (
                "Aether: A browser permission request "
                "is already waiting.\n"
                'Say "yes" to approve or "no" to cancel it first.'
            )

        site = (
            match.group(1)
            .strip()
            .strip('"')
        )

        goal = (
            match.group(2)
            .strip()
            .strip('"')
            .rstrip(".")
            .strip()
        )

        if not goal:

            return (
                "Aether: Browser goal agent stopped.\n"
                "No navigation goal was provided."
            )

        page = self._prepare_goal_page(
            site
        )

        if not page.get(
            "success",
            False,
        ):

            return page.get(
                "response",
                (
                    "Aether: Browser goal agent "
                    "could not prepare the page."
                ),
            )

        self.agent_goal = {
            "goal": goal,
            "site": site,
            "hops": 0,
            "max_hops": self.agent_max_hops,
            "history": [],
            "visited_pages": [],
        }

        snapshot = {
            "success": True,
            "title": page.get(
                "title",
                "",
            ),
            "url": page.get(
                "url",
                "",
            ),
            "elements": page.get(
                "elements",
                [],
            ),
            "visible_text": (
                self._agent_visible_page_text()
            ),
        }

        return self._agent_continue_from_snapshot(
            snapshot
        )

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
                pending = self.permissions.take()

                is_agent_action = bool(
                    isinstance(
                        pending,
                        dict,
                    )
                    and pending.get(
                        "data",
                        {},
                    ).get(
                        "_agent_goal",
                        False,
                    )
                )

                self.last_execution_result = {
                    "success": False,
                    "cancelled": True,
                    "response": (
                        "Aether: Browser action cancelled."
                    ),
                }

                if is_agent_action:

                    self.agent_goal = None

                    return (
                        "Aether: Browser goal cancelled."
                    )

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

            is_agent_action = bool(
                data.pop(
                    "_agent_goal",
                    False,
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

            if not is_agent_action:

                return self._format_result(
                    result
                )

            if not result.get(
                "success",
                False,
            ):
                self.agent_goal = None

                return self._format_result(
                    result
                )

            if self.agent_goal is None:

                return self._format_result(
                    result
                )

            self.agent_goal[
                "hops"
            ] = (
                int(
                    self.agent_goal.get(
                        "hops",
                        0,
                    )
                )
                + 1
            )

            action_response = (
                self._format_result(
                    result
                )
            )

            continuation_response = (
                self._continue_browser_agent()
            )

            return (
                action_response
                + "\n\n"
                + continuation_response
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
