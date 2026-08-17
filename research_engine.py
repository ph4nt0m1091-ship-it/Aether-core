import re
from collections import Counter


class ResearchEngine:
    """
    Analyzes web research results for Aether.

    ResearchEngine does not perform web searches itself.
    It receives search results and organizes the evidence
    into a structured research report.
    """

    STOP_WORDS = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "are",
        "was",
        "were",
        "have",
        "has",
        "had",
        "into",
        "they",
        "their",
        "them",
        "which",
        "what",
        "when",
        "where",
        "while",
        "about",
        "also",
        "can",
        "could",
        "would",
        "should",
        "will",
        "your",
        "you",
        "our",
        "out",
        "use",
        "used",
        "using",
        "than",
        "then",
        "there",
        "these",
        "those",
        "such",
        "more",
        "most",
        "other",
        "some",
        "each"
    }

    IRREGULAR_NORMALIZATION = {
        "motors": "motor",
        "drivers": "driver",
        "controllers": "controller",
        "robots": "robot",
        "batteries": "battery",
        "motors": "motor",
        "devices": "device",
        "systems": "system",
        "signals": "signal",
        "transistors": "transistor",
        "circuits": "circuit"
    }

    PROTECTED_WORDS = {
        "analysis",
        "physics",
        "electronics",
        "robotics",
        "news",
        "series",
        "species",
        "status"
    }

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
                        "content": content,
                        "keywords": self._extract_keywords(
                            content
                        )
                    }
                )

        shared_topics = self._find_shared_topics(
            evidence
        )

        evidence_summary = self._build_evidence_summary(
            evidence,
            shared_topics
        )

        return {
            "query": query,
            "summary": answer,
            "evidence": evidence,
            "sources": sources,
            "source_count": len(sources),
            "shared_topics": shared_topics,
            "evidence_summary": evidence_summary
        }

    # ---------------------------------
    # WORD NORMALIZATION
    # ---------------------------------

    def _normalize_word(self, word):
        """
        Normalize simple plural forms into a shared concept.

        This intentionally stays conservative so words such
        as physics, electronics, analysis, and robotics are
        not incorrectly modified.
        """

        word = word.lower().strip()

        if not word:

            return word

        if word in self.PROTECTED_WORDS:

            return word

        if word in self.IRREGULAR_NORMALIZATION:

            return self.IRREGULAR_NORMALIZATION[
                word
            ]

        # batteries -> battery
        if (
            word.endswith("ies")
            and len(word) > 4
        ):

            return (
                word[:-3]
                + "y"
            )

        # controllers -> controller
        # drivers -> driver
        # motors -> motor
        #
        # Avoid words ending with:
        # ss, us, is
        if (
            word.endswith("s")
            and len(word) > 4
            and not word.endswith(
                (
                    "ss",
                    "us",
                    "is"
                )
            )
        ):

            return word[:-1]

        return word

    # ---------------------------------
    # KEYWORD EXTRACTION
    # ---------------------------------

    def _extract_keywords(
        self,
        text,
        limit=12
    ):
        """
        Extract useful repeated terms from source content.
        """

        words = re.findall(
            r"[a-zA-Z][a-zA-Z0-9\-]+",
            text.lower()
        )

        normalized = []

        for word in words:

            if (
                len(word) < 4
                or word in self.STOP_WORDS
            ):

                continue

            normalized_word = (
                self._normalize_word(
                    word
                )
            )

            if (
                not normalized_word
                or normalized_word
                in self.STOP_WORDS
            ):

                continue

            normalized.append(
                normalized_word
            )

        counts = Counter(
            normalized
        )

        return [
            word
            for word, _ in counts.most_common(
                limit
            )
        ]

    # ---------------------------------
    # CROSS-SOURCE TOPICS
    # ---------------------------------

    def _find_shared_topics(
        self,
        evidence,
        limit=10
    ):
        """
        Find normalized keywords that appear
        across multiple sources.
        """

        topic_counts = Counter()

        for item in evidence:

            unique_keywords = set(
                item.get(
                    "keywords",
                    []
                )
            )

            for keyword in unique_keywords:

                topic_counts[keyword] += 1

        shared = []

        for keyword, count in topic_counts.most_common():

            if count < 2:

                continue

            shared.append(
                {
                    "topic": keyword,
                    "sources": count
                }
            )

            if len(shared) >= limit:

                break

        return shared

    # ---------------------------------
    # EVIDENCE SUMMARY
    # ---------------------------------

    def _build_evidence_summary(
        self,
        evidence,
        shared_topics
    ):
        """
        Build a basic evidence overview from multiple sources.
        """

        if not evidence:

            return (
                "No source evidence was available."
            )

        source_count = len(
            evidence
        )

        if not shared_topics:

            return (
                f"{source_count} sources were analyzed, "
                "but no strong repeated topics were found."
            )

        topic_text = ", ".join(
            item["topic"]
            for item in shared_topics[:5]
        )

        return (
            f"{source_count} sources were analyzed. "
            f"Common topics across the evidence include: "
            f"{topic_text}."
        )
