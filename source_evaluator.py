from urllib.parse import urlparse


class SourceEvaluator:
    """
    Evaluates research sources for Aether.

    This is a heuristic quality signal, not a guarantee
    that a source is accurate or trustworthy.
    """

    HIGH_VALUE_DOMAINS = {
        "gov": 3,
        "edu": 3
    }

    REFERENCE_DOMAINS = {
        "docs.python.org",
        "developer.mozilla.org"
    }

    COMMUNITY_DOMAINS = {
        "reddit.com",
        "quora.com"
    }

    VIDEO_DOMAINS = {
        "youtube.com",
        "youtu.be"
    }

    def evaluate(self, source):
        """
        Return quality information for one source.
        """

        title = source.get(
            "title",
            ""
        ).strip()

        url = source.get(
            "url",
            ""
        ).strip()

        domain = self._get_domain(
            url
        )

        score = 5
        reasons = []

        # Government and education sources.
        if domain.endswith(".gov"):

            score += self.HIGH_VALUE_DOMAINS[
                "gov"
            ]

            reasons.append(
                "government domain"
            )

        elif domain.endswith(".edu"):

            score += self.HIGH_VALUE_DOMAINS[
                "edu"
            ]

            reasons.append(
                "educational domain"
            )

        # Known technical documentation.
        if domain in self.REFERENCE_DOMAINS:

            score += 2

            reasons.append(
                "technical documentation"
            )

        # Community-generated information can still
        # be useful, but should usually be verified.
        if (
            domain in self.COMMUNITY_DOMAINS
            or any(
                domain.endswith(
                    "." + community
                )
                for community
                in self.COMMUNITY_DOMAINS
            )
        ):

            score -= 1

            reasons.append(
                "community-generated source"
            )

        # Video sources can be useful evidence,
        # but quality varies substantially.
        if (
            domain in self.VIDEO_DOMAINS
            or any(
                domain.endswith(
                    "." + video_domain
                )
                for video_domain
                in self.VIDEO_DOMAINS
            )
        ):

            score -= 1

            reasons.append(
                "video source"
            )

        score = max(
            1,
            min(
                score,
                10
            )
        )

        if score >= 8:

            rating = "strong"

        elif score >= 5:

            rating = "moderate"

        else:

            rating = "verify"

        return {
            "title": title,
            "url": url,
            "domain": domain,
            "quality_score": score,
            "quality_rating": rating,
            "quality_reasons": reasons
        }

    def evaluate_all(self, sources):
        """
        Evaluate multiple research sources.
        """

        return [
            self.evaluate(source)
            for source in sources
            if isinstance(
                source,
                dict
            )
        ]

    def _get_domain(self, url):
        """
        Extract and normalize a domain from a URL.
        """

        try:

            domain = urlparse(
                url
            ).netloc.lower()

        except (TypeError, ValueError):

            return ""

        if domain.startswith("www."):

            domain = domain[4:]

        return domain