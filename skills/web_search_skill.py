from tools.web_search_tool import WebSearchTool


class WebSearchSkill:
    """
    Handles web search and web research requests for Aether.
    """

    name = "web_search"

    description = (
        "Searches the web for information and "
        "returns an answer with supporting sources."
    )

    def __init__(self, memory):

        self.memory = memory

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

        query = None

        for prefix in prefixes:

            if message.lower().startswith(prefix):

                query = message[
                    len(prefix):
                ].strip()

                break

        if query is None:

            return None

        if not query:

            return (
                "Aether: What would you "
                "like me to search for?"
            )

        # ---------------------------------
        # Search + synthesized answer
        # ---------------------------------

        search_data = self.tool.search_with_answer(
            query,
            max_results=5
        )

        answer = search_data.get(
            "answer",
            ""
        ).strip()

        results = search_data.get(
            "results",
            []
        )

        # ---------------------------------
        # Fallback
        # ---------------------------------

        if not answer and not results:

            return (
                "Aether: I couldn't find "
                "any useful web results."
            )

        # ---------------------------------
        # Build Response
        # ---------------------------------

        output = (
            f"Aether: Here's what I found "
            f"for: {query}\n\n"
        )

        if answer:

            output += (
                f"{answer}\n\n"
            )

        # ---------------------------------
        # Sources
        # ---------------------------------

        if results:

            output += "Sources:\n"

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

                output += (
                    f"{index}. {title}\n"
                )

                if url:

                    output += (
                        f"   {url}\n"
                    )

        return output.rstrip()

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(self, step):
        """
        WebSearchSkill is not used by
        missions yet.
        """

        return None