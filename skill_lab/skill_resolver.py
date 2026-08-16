class SkillResolver:
    """
    Determines whether Aether can resolve a Skill Gap.

    The resolver does not modify the system or install anything.
    It only determines whether a known resolution strategy exists.
    """

    def __init__(self):

        self.resolution_strategies = {
            "web_search": self.resolve_web_search
        }

    # ---------------------------------
    # RESOLVE
    # ---------------------------------

    def resolve(self, gap):

        strategy = self.resolution_strategies.get(
            gap.capability
        )

        if strategy is None:

            return None

        return strategy(gap)

    # ---------------------------------
    # WEB SEARCH
    # ---------------------------------

    def resolve_web_search(self, gap):
        """
        Prepare a resolution for web search.

        This does not perform a web search yet.
        It only identifies the capability as resolvable.
        """

        return {
            "capability": "web_search",
            "status": "ready",
            "resolution": "web_search_skill"
        }

    # ---------------------------------
    # AVAILABLE RESOLUTIONS
    # ---------------------------------

    def available_resolutions(self):

        return list(
            self.resolution_strategies.keys()
        )