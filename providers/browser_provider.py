from urllib.parse import urlparse

from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


class BrowserProvider:
    """
    Local Chromium browser control using Playwright.

    Browser v1 principles:
    - Real DOM / accessibility targeting
    - No blind screen coordinates
    - http/https navigation only
    - Exact element matching
    - Password fields blocked
    - Fill/click require explicit permission
    """

    name = "browser"
    provider_type = "local_browser"
    requires_permission = True

    MAX_TEXT_LENGTH = 1000
    MAX_ELEMENTS = 100

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    # ---------------------------------
    # PROVIDER INTERFACE
    # ---------------------------------

    def available(self):
        try:
            import playwright  # noqa: F401
            return True
        except ImportError:
            return False

    def capabilities(self):
        return [
            "browser_navigate",
            "browser_inspect",
            "browser_fill",
            "browser_click",
            "browser_status",
            "browser_close",
        ]

    def info(self):
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "available": self.available(),
            "capabilities": self.capabilities(),
            "requires_permission": self.requires_permission,
            "coordinate_click": False,
        }

    def execute(self, capability, task):
        task = (
            task
            if isinstance(task, dict)
            else {}
        )

        handlers = {
            "browser_navigate": self._navigate,
            "browser_inspect": self._inspect,
            "browser_fill": self._fill,
            "browser_click": self._click,
            "browser_status": self._status,
            "browser_close": self._close,
        }

        handler = handlers.get(capability)

        if handler is None:
            return self._failure(
                f'Unsupported browser capability: "{capability}".'
            )

        try:
            return handler(task)

        except PlaywrightTimeoutError:
            return self._failure(
                "The browser action timed out before the page "
                "or element became ready."
            )

        except PlaywrightError as error:
            return self._failure(
                f"Browser automation error: {error}"
            )

        except Exception as error:
            return self._failure(
                f"Browser action failed: {error}"
            )

    # ---------------------------------
    # SESSION
    # ---------------------------------

    def _reset_session_handles(self):
        self._page = None
        self._context = None
        self._browser = None

    def _ensure_page(self):
        # First verify the browser process itself is still alive.
        # A Page object can sometimes remain in Python after the
        # user manually closes the Chromium window.
        if self._browser is not None:

            try:
                if not self._browser.is_connected():
                    self._reset_session_handles()

            except PlaywrightError:
                self._reset_session_handles()

        # Only reuse a page after actively proving that the
        # Playwright connection still works. After a user closes
        # Chromium manually, is_closed() can briefly report False
        # even though the underlying browser target is already gone.
        if self._page is not None:

            try:
                if not self._page.is_closed():

                    # Harmless connection probe.
                    self._page.title()

                    return self._page

            except PlaywrightError:
                self._reset_session_handles()

            self._page = None

        if self._playwright is None:
            self._playwright = sync_playwright().start()

        if self._browser is None:
            self._browser = (
                self._playwright.chromium.launch(
                    headless=False
                )
            )

        # A context can also become unusable after an external
        # browser-window close. Try it once, then rebuild the
        # browser session conservatively if needed.
        if self._context is None:
            self._context = self._browser.new_context()

        try:
            self._page = self._context.new_page()

        except PlaywrightError:

            self._reset_session_handles()

            self._browser = (
                self._playwright.chromium.launch(
                    headless=False
                )
            )

            self._context = (
                self._browser.new_context()
            )

            self._page = (
                self._context.new_page()
            )

        return self._page

    # ---------------------------------
    # NAVIGATE
    # ---------------------------------

    def _navigate(self, task):
        url = str(
            task.get("url", "")
        ).strip()

        if not url:
            return self._failure(
                "No browser URL was provided."
            )

        if "://" not in url:
            url = "https://" + url

        parsed = urlparse(url)

        if parsed.scheme not in (
            "http",
            "https",
        ):
            return self._failure(
                "Browser v1 only allows http and https URLs."
            )

        if not parsed.netloc:
            return self._failure(
                "That browser URL is not valid."
            )

        page = self._ensure_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        return {
            "success": True,
            "url": page.url,
            "title": page.title(),
            "response": (
                f'Opened "{page.title() or page.url}".\n'
                f"URL: {page.url}"
            ),
        }

    # ---------------------------------
    # INSPECT
    # ---------------------------------

    def _inspect(self, task):
        page = self._ensure_page()

        elements = page.locator(
            "button, a, input, textarea, select, "
            "[role='button'], [role='link'], "
            "[contenteditable='true']"
        )

        count = min(
            elements.count(),
            self.MAX_ELEMENTS,
        )

        found = []

        for index in range(count):
            locator = elements.nth(index)

            try:
                if not locator.is_visible():
                    continue

                data = locator.evaluate(
                    """element => ({
                        tag: (element.tagName || '').toLowerCase(),
                        text: (element.innerText || element.value || '').trim(),
                        ariaLabel: element.getAttribute('aria-label') || '',
                        placeholder: element.getAttribute('placeholder') || '',
                        name: element.getAttribute('name') || '',
                        id: element.id || '',
                        type: element.getAttribute('type') || '',
                        role: element.getAttribute('role') || ''
                    })"""
                )

                label = (
                    data.get("ariaLabel")
                    or data.get("placeholder")
                    or data.get("text")
                    or data.get("name")
                    or data.get("id")
                    or "(unnamed)"
                )

                label = " ".join(
                    str(label).split()
                )

                if len(label) > 120:
                    label = label[:117] + "..."

                found.append(
                    {
                        "label": label,
                        "tag": data.get("tag", ""),
                        "role": data.get("role", ""),
                        "type": data.get("type", ""),
                        "id": data.get("id", ""),
                        "name": data.get("name", ""),
                    }
                )

            except PlaywrightError:
                continue

        return {
            "success": True,
            "url": page.url,
            "title": page.title(),
            "count": len(found),
            "elements": found,
        }

    # ---------------------------------
    # EXACT FIELD MATCHING
    # ---------------------------------

    def _field_candidates(self):
        page = self._ensure_page()

        return page.locator(
            "input, textarea, select, "
            "[contenteditable='true']"
        )

    def _field_metadata(self, locator):
        return locator.evaluate(
            """element => {
                let labelText = '';

                if (element.labels && element.labels.length) {
                    labelText = Array.from(element.labels)
                        .map(label => (label.innerText || '').trim())
                        .filter(Boolean)
                        .join(' ');
                }

                return {
                    tag: (element.tagName || '').toLowerCase(),
                    type: (element.getAttribute('type') || '').toLowerCase(),
                    ariaLabel: element.getAttribute('aria-label') || '',
                    placeholder: element.getAttribute('placeholder') || '',
                    name: element.getAttribute('name') || '',
                    id: element.id || '',
                    label: labelText
                };
            }"""
        )

    def _exact_field_matches(self, field_name):
        wanted = field_name.strip().lower()

        matches = []

        fields = self._field_candidates()

        for index in range(fields.count()):
            locator = fields.nth(index)

            try:
                if not locator.is_visible():
                    continue

                data = self._field_metadata(locator)

                values = {
                    str(data.get("ariaLabel", "")).strip().lower(),
                    str(data.get("placeholder", "")).strip().lower(),
                    str(data.get("name", "")).strip().lower(),
                    str(data.get("id", "")).strip().lower(),
                    str(data.get("label", "")).strip().lower(),
                }

                values.discard("")

                if wanted in values:
                    matches.append(
                        (
                            locator,
                            data,
                        )
                    )

            except PlaywrightError:
                continue

        return matches

    # ---------------------------------
    # FILL
    # ---------------------------------

    def _fill(self, task):
        if not task.get(
            "permission_granted",
            False,
        ):
            return self._failure(
                "Browser fill requires explicit permission.",
                requires_permission=True,
            )

        field = str(
            task.get("field", "")
        ).strip()

        text = str(
            task.get("text", "")
        )

        if not field:
            return self._failure(
                "No browser field name was provided."
            )

        if len(text) > self.MAX_TEXT_LENGTH:
            return self._failure(
                f"Browser text is limited to "
                f"{self.MAX_TEXT_LENGTH} characters."
            )

        matches = self._exact_field_matches(
            field
        )

        if len(matches) != 1:
            return self._failure(
                f'I could not find exactly one visible field '
                f'named "{field}". I will not guess.'
            )

        locator, data = matches[0]

        if data.get("type") == "password":
            return self._failure(
                "Browser v1 will not type into password fields."
            )

        tag = data.get("tag")

        if tag == "select":
            return self._failure(
                "Browser v1 does not fill select menus yet."
            )

        locator.fill(text)

        return {
            "success": True,
            "field": field,
            "character_count": len(text),
            "url": self._ensure_page().url,
            "response": (
                f'Filled "{field}" with '
                f"{len(text)} characters.\n"
                "No submit action was sent."
            ),
        }

    # ---------------------------------
    # EXACT CLICK MATCHING
    # ---------------------------------

    def _click_candidates(self):
        page = self._ensure_page()

        return page.locator(
            "button, a, "
            "[role='button'], [role='link'], "
            "input[type='button'], "
            "input[type='submit']"
        )

    def _click_metadata(self, locator):
        return locator.evaluate(
            """element => ({
                tag: (element.tagName || '').toLowerCase(),
                text: (element.innerText || element.value || '').trim(),
                ariaLabel: element.getAttribute('aria-label') || '',
                title: element.getAttribute('title') || '',
                id: element.id || '',
                name: element.getAttribute('name') || '',
                type: (element.getAttribute('type') || '').toLowerCase(),
                href: element.href || ''
            })"""
        )

    def _exact_click_matches(self, target):
        wanted = target.strip().lower()

        matches = []

        elements = self._click_candidates()

        for index in range(elements.count()):
            locator = elements.nth(index)

            try:
                if not locator.is_visible():
                    continue

                if not locator.is_enabled():
                    continue

                data = self._click_metadata(
                    locator
                )

                values = {
                    str(data.get("text", "")).strip().lower(),
                    str(data.get("ariaLabel", "")).strip().lower(),
                    str(data.get("title", "")).strip().lower(),
                    str(data.get("id", "")).strip().lower(),
                    str(data.get("name", "")).strip().lower(),
                }

                values.discard("")

                if wanted in values:
                    matches.append(
                        (
                            locator,
                            data,
                        )
                    )

            except PlaywrightError:
                continue

        return matches

    # ---------------------------------
    # CLICK
    # ---------------------------------

    def _click(self, task):
        if not task.get(
            "permission_granted",
            False,
        ):
            return self._failure(
                "Browser click requires explicit permission.",
                requires_permission=True,
            )

        target = str(
            task.get("target", "")
        ).strip()

        if not target:
            return self._failure(
                "No browser element name was provided."
            )

        matches = self._exact_click_matches(
            target
        )

        if len(matches) != 1:

            # Multiple visible links with the exact same name
            # are allowed only when every match resolves to
            # the same non-empty destination URL.
            #
            # Example:
            # desktop + responsive navigation may expose two
            # "Documentation" links that both go to the same
            # documentation page.
            #
            # Different destinations remain ambiguous and are
            # refused rather than guessed.

            if len(matches) > 1:

                hrefs = {
                    str(
                        data.get(
                            "href",
                            "",
                        )
                    ).strip()
                    for _, data in matches
                    if str(
                        data.get(
                            "href",
                            "",
                        )
                    ).strip()
                }

                all_are_links = all(
                    str(
                        data.get(
                            "tag",
                            "",
                        )
                    ).lower()
                    == "a"
                    for _, data in matches
                )

                if (
                    all_are_links
                    and len(hrefs) == 1
                ):

                    locator, data = (
                        matches[0]
                    )

                else:

                    return self._failure(
                        f'I found {len(matches)} enabled visible '
                        f'elements named "{target}" with '
                        "different or unverifiable destinations. "
                        "I will not guess."
                    )

            else:

                return self._failure(
                    f'I could not find exactly one enabled visible '
                    f'element named "{target}". I will not guess.'
                )

        else:

            locator, data = matches[0]

        before_url = self._ensure_page().url

        locator.click(
            timeout=10000
        )

        self._ensure_page().wait_for_timeout(
            250
        )

        after_url = self._ensure_page().url

        return {
            "success": True,
            "target": target,
            "before_url": before_url,
            "url": after_url,
            "element_type": data.get(
                "type",
                "",
            ),
            "response": (
                f'Clicked exact browser element "{target}".\n'
                "No screen coordinates were used."
            ),
        }

    # ---------------------------------
    # STATUS
    # ---------------------------------

    def _status(self, task):
        if (
            self._page is None
            or self._page.is_closed()
        ):
            return {
                "success": True,
                "running": False,
                "response": (
                    "Browser session is not running."
                ),
            }

        return {
            "success": True,
            "running": True,
            "url": self._page.url,
            "title": self._page.title(),
            "response": (
                "Browser session is running.\n"
                f"Title: {self._page.title()}\n"
                f"URL: {self._page.url}"
            ),
        }

    # ---------------------------------
    # CLOSE
    # ---------------------------------

    def _close(self, task):
        if self._context is not None:
            try:
                self._context.close()
            except PlaywrightError:
                pass

        if self._browser is not None:
            try:
                self._browser.close()
            except PlaywrightError:
                pass

        if self._playwright is not None:
            try:
                self._playwright.stop()
            except PlaywrightError:
                pass

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

        return {
            "success": True,
            "response": "Browser session closed.",
        }

    # ---------------------------------
    # RESULT
    # ---------------------------------

    def _failure(
        self,
        error,
        requires_permission=False,
    ):
        return {
            "success": False,
            "error": error,
            "requires_permission": (
                requires_permission
            ),
        }
