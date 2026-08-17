from research_engine import ResearchEngine
from tools.web_search_tool import WebSearchTool


class ResearchSkill:
    """
    Performs structured web research for Aether.

    ResearchSkill gathers web information and sends
    it through ResearchEngine for structured analysis.
    """

    name = "research"

    description = (
        "Researches a topic using web sources and "
        "returns findings with supporting evidence."
    )

    def __init__(self, memory):

        self.memory = memory

        self.tool = WebSearchTool()

        self.engine = ResearchEngine()

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

        search_data = self.tool.search_with_answer(
            query,
            max_results=5
        )

        # ---------------------------------
        # Analyze Research
        # ---------------------------------

        research = self.engine.analyze(
            query,
            search_data
        )

        summary = research.get(
            "summary",
            ""
        ).strip()

        sources = research.get(
            "sources",
            []
        )

        source_count = research.get(
            "source_count",
            0
        )

        shared_topics = research.get(
            "shared_topics",
            []
        )

        evidence_summary = research.get(
            "evidence_summary",
            ""
        ).strip()

        if not summary and not sources:

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

        # ---------------------------------
        # Main Findings
        # ---------------------------------

        if summary:

            output += (
                "Findings:\n"
                f"{summary}\n\n"
            )

        # ---------------------------------
        # Evidence Analysis
        # ---------------------------------

        if evidence_summary:

            output += (
                "Evidence analysis:\n"
                f"{evidence_summary}\n\n"
            )

        # ---------------------------------
        # Shared Topics
        # ---------------------------------

        if shared_topics:

            output += (
                "Shared topics across sources:\n"
            )

            for item in shared_topics[:5]:

                topic = item.get(
                    "topic",
                    ""
                )

                count = item.get(
                    "sources",
                    0
                )

                if not topic:

                    continue

                output += (
                    f"- {topic} "
                    f"({count} sources)\n"
                )

            output += "\n"

        # ---------------------------------
        # Sources
        # ---------------------------------

        if sources:

            output += (
                f"Sources analyzed: "
                f"{source_count}\n"
            )

            for index, source in enumerate(
                sources,
                start=1
            ):

                title = source.get(
                    "title",
                    "Untitled"
                )

                url = source.get(
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