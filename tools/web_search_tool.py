import os

from tavily import TavilyClient


class WebSearchTool:
    """
    Performs web searches using Tavily.

    The Tavily API key is loaded from the
    TAVILY_API_KEY environment variable.
    """

    def __init__(self):

        self.api_key = os.getenv(
            "TAVILY_API_KEY"
        )

        self.client = None

        if self.api_key:

            self.client = TavilyClient(
                api_key=self.api_key
            )

    # ---------------------------------
    # SEARCH
    # ---------------------------------

    def search(
        self,
        query,
        max_results=5
    ):

        query = query.strip()

        if not query:

            return []

        if not self.client:

            print(
                "WebSearchTool: "
                "TAVILY_API_KEY is not configured."
            )

            return []

        try:

            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer="basic"
            )

        except Exception as error:

            print(
                f"WebSearchTool error: {error}"
            )

            return []

        results = []

        for result in response.get(
            "results",
            []
        ):

            if not isinstance(
                result,
                dict
            ):

                continue

            title = result.get(
                "title",
                ""
            )

            url = result.get(
                "url",
                ""
            )

            content = result.get(
                "content",
                ""
            )

            if not title and not url:

                continue

            results.append(
                {
                    "title": title,
                    "url": url,
                    "content": content
                }
            )

            if len(results) >= max_results:

                break

        return results

    # ---------------------------------
    # ANSWER
    # ---------------------------------

    def search_with_answer(
        self,
        query,
        max_results=5
    ):

        query = query.strip()

        if not query:

            return {
                "answer": "",
                "results": []
            }

        if not self.client:

            return {
                "answer": "",
                "results": []
            }

        try:

            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer="basic"
            )

        except Exception as error:

            print(
                f"WebSearchTool error: {error}"
            )

            return {
                "answer": "",
                "results": []
            }

        results = []

        for result in response.get(
            "results",
            []
        ):

            if not isinstance(
                result,
                dict
            ):

                continue

            results.append(
                {
                    "title": result.get(
                        "title",
                        ""
                    ),
                    "url": result.get(
                        "url",
                        ""
                    ),
                    "content": result.get(
                        "content",
                        ""
                    )
                }

            )

            if len(results) >= max_results:

                break

        return {
            "answer": response.get(
                "answer",
                ""
            ),
            "results": results
        }