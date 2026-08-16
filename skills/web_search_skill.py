from tools.web_search_tool import WebSearchTool


class WebSearchSkill:
    """
    Handles web search requests for Aether.
    """

    name = "web_search"

    description = (
        "Searches the web for information."
    )

    def __init__(self, memory):

        self.memory = memory

        # Web search engine
        self.tool = WebSearchTool()

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(self, message):

        message = message.strip()

        prefixes = [
            "search the web for ",
            "search web for ",
            "search for ",
            "look up ",
            "look online for "
        ]

        for prefix in prefixes:

            if message.lower().startswith(prefix):

                query = message[
                    len(prefix):
                ].strip()

                if not query:

                    return (
                        "Aether: What would you "
                        "like me to search for?"
                    )

                results = self.tool.search(
                    query
                )

                if not results:

                    return (
                        "Aether: I couldn't find "
                        "any search results."
                    )

                output = (
                    f"Aether: I found "
                    f"{len(results)} results "
                    f"for: {query}\n\n"
                )

                for index, result in enumerate(
                    results,
                    start=1
                ):

                    title = result.get(
                        "title",
                        "Untitled"
                    )

                    url = result.get(
                        "url",
                        ""
                    )

                    content = result.get(
                        "content",
                        ""
                    )

                    output += (
                        f"{index}. {title}\n"
                        f"   {url}\n"
                    )

                    if content:

                        # Keep terminal output readable.
                        summary = (
                            content
                            .replace("\n", " ")
                            .strip()
                        )

                        if len(summary) > 300:

                            summary = (
                                summary[:300]
                                + "..."
                            )

                        output += (
                            f"   {summary}\n"
                        )

                    output += "\n"

                return output.rstrip()

        return None

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(self, step):
        """
        WebSearchSkill is not used by
        missions yet.
        """

        return None