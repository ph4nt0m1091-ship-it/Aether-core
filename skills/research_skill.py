from tools.web_search_tool import WebSearchTool


class ResearchSkill:
    """
    Performs structured web research for Aether.

    ResearchSkill uses web search results and a synthesized
    answer to produce a cleaner research-style response.
    """

    name = "research"

    description = (
        "Researches a topic using web sources and "
        "returns findings with supporting sources."
    )

    def __init__(self, memory):

        self.memory = memory
        self.tool = WebSearchTool()

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(self, message):

        message = message.strip()
        lower = message.lower()

        prefixes = [
            "research ",
            "research the ",
            "research about ",
            "do research on "
        ]

        query = None

        for prefix in prefixes:

            if lower.startswith(prefix):

                query = message[
                    len(prefix):
                ].strip()

                break

        if query is None:

            return None

        if not query:

            return (
                "Aether: What would you "
                "like me to research?"
            )

        # ---------------------------------
        # Gather Research
        # ---------------------------------

        research = self.tool.search_with_answer(
            query,
            max_results=5
        )

        answer = research.get(
            "answer",
            ""
        ).strip()

        results = research.get(
            "results",
            []
        )

        if not answer and not results:

            return (
                "Aether: I couldn't find enough "
                "information to research that topic."
            )

        # ---------------------------------
        # Build Research Report
        # ---------------------------------

        output = (
            f"Aether: Researching: {query}\n\n"
        )

        if answer:

            output += (
                "Findings:\n"
                f"{answer}\n\n"
            )

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

        output += (
            "\nResearch status: complete."
        )

        return output

    # ---------------------------------
    # EXECUTE
    # ---------------------------------

    def execute(self, step):
        """
        ResearchSkill is not used by missions yet.
        """

        return None