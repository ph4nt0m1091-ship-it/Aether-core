class ResearchEngine:
    """
    Analyzes web research results for Aether.

    ResearchEngine does not perform web searches itself.
    It receives search results and organizes the evidence
    into a structured research report.
    """

    def analyze(self, query, search_data):
        """
        Analyze search results and return structured research.
        """

        answer = search_data.get(
            "answer",
            ""
        ).strip()

        results = search_data.get(
            "results",
            []
        )

        sources = []
        evidence = []

        for result in results:

            if not isinstance(
                result,
                dict
            ):

                continue

            title = result.get(
                "title",
                ""
            ).strip()

            url = result.get(
                "url",
                ""
            ).strip()

            content = result.get(
                "content",
                ""
            ).strip()

            sources.append(
                {
                    "title": title,
                    "url": url
                }
            )

            if content:

                evidence.append(
                    {
                        "title": title,
                        "content": content
                    }
                )

        return {
            "query": query,
            "summary": answer,
            "evidence": evidence,
            "sources": sources,
            "source_count": len(sources)
        }