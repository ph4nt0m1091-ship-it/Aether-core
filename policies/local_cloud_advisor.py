from model_router import (
    ModelRouter
)

from policies.cloud_routing_policy import (
    CloudRoutingPolicy
)


class LocalCloudAdvisor:
    """
    Aether Local vs Cloud Decision Engine v2.

    This engine is advisory only.

    It considers:
    - privacy/local context
    - explicit cloud/local intent
    - task complexity
    - live installed local models
    - local model tier
    - whether cloud may add meaningful value

    It NEVER executes:
    - Ollama
    - OpenRouter
    - any external provider
    """

    def __init__(
        self
    ):

        self.local_router = (
            ModelRouter()
        )

        self.cloud_router = (
            CloudRoutingPolicy()
        )

        self.heavy_keywords = (
            "deep analysis",
            "deeply analyze",
            "very complex",
            "extremely complex",
            "large architecture",
            "multiple architectures",
            "second opinion",
            "another ai opinion",
            "compare many",
            "many approaches",
            "advanced reasoning",
            "long detailed analysis"
        )

    # ---------------------------------
    # COMPLEXITY
    # ---------------------------------

    def _complexity_score(
        self,
        prompt
    ):

        lower = (
            prompt.lower()
        )

        score = 0

        for keyword in (
            self.local_router
            .COMPLEX_KEYWORDS
        ):

            if keyword in lower:

                score += 1

        for keyword in (
            self.heavy_keywords
        ):

            if keyword in lower:

                score += 2

        if len(
            prompt
        ) > 500:

            score += 1

        if len(
            prompt
        ) > 1500:

            score += 2

        return score

    # ---------------------------------
    # CLOUD BENEFIT
    # ---------------------------------

    def _cloud_benefit(
        self,
        prompt,
        cloud_decision,
        local_decision
    ):

        route = (
            cloud_decision.get(
                "route"
            )
        )

        reason = (
            cloud_decision.get(
                "reason"
            )
        )

        if route == (
            CloudRoutingPolicy
            .ROUTE_BLOCK_CLOUD
        ):

            return {
                "level": "blocked",
                "reason": (
                    "cloud is blocked for this request"
                )
            }

        if (
            route
            == CloudRoutingPolicy.ROUTE_LOCAL
            and reason
            == "possible_private_or_local_context"
        ):

            return {
                "level": "restricted",
                "reason": (
                    "local/private context should "
                    "remain on-device"
                )
            }

        if route == (
            CloudRoutingPolicy
            .ROUTE_CLOUD
        ):

            return {
                "level": "requested",
                "reason": (
                    "cloud was explicitly requested"
                )
            }

        if route == (
            CloudRoutingPolicy
            .ROUTE_SUGGEST_CLOUD
        ):

            return {
                "level": "high",
                "reason": (
                    "the request may benefit from "
                    "stronger cloud reasoning"
                )
            }

        complexity = (
            self._complexity_score(
                prompt
            )
        )

        local_tier = (
            local_decision.get(
                "tier"
            )
            if local_decision.get(
                "success"
            )
            else None
        )

        if not (
            local_decision.get(
                "success"
            )
        ):

            return {
                "level": "high",
                "reason": (
                    "no suitable local model "
                    "was detected"
                )
            }

        if (
            complexity >= 5
            and local_tier in (
                "fast",
                "smart"
            )
        ):

            return {
                "level": "medium",
                "reason": (
                    "the task is demanding enough "
                    "that cloud may provide a stronger "
                    "second option"
                )
            }

        return {
            "level": "low",
            "reason": (
                "a capable local model is available"
            )
        }

    # ---------------------------------
    # ADVISE
    # ---------------------------------

    def advise(
        self,
        prompt,
        installed_models
    ):

        prompt = str(
            prompt or ""
        ).strip()

        installed_models = list(
            installed_models or []
        )

        cloud_decision = (
            self.cloud_router
            .decide(
                prompt
            )
        )

        local_decision = (
            self.local_router
            .choose(
                prompt,
                installed_models
            )
        )

        complexity = (
            self._complexity_score(
                prompt
            )
        )

        cloud_benefit = (
            self._cloud_benefit(
                prompt,
                cloud_decision,
                local_decision
            )
        )

        cloud_route = (
            cloud_decision.get(
                "route",
                "local"
            )
        )

        cloud_reason = (
            cloud_decision.get(
                "reason",
                "local_default"
            )
        )

        local_success = bool(
            local_decision.get(
                "success"
            )
        )

        local_model = (
            local_decision.get(
                "model"
            )
            if local_success
            else None
        )

        local_tier = (
            local_decision.get(
                "tier"
            )
            if local_success
            else None
        )

        # ---------------------------------
        # HARD CLOUD BLOCK
        # ---------------------------------

        if cloud_route == (
            CloudRoutingPolicy
            .ROUTE_BLOCK_CLOUD
        ):

            recommendation = (
                "local"
            )

            recommendation_label = (
                "LOCAL"
            )

            reason = (
                "cloud is blocked because the "
                "request may contain a secret "
                "or credential"
            )

        # ---------------------------------
        # PRIVATE / LOCAL
        # ---------------------------------

        elif (
            cloud_route
            == CloudRoutingPolicy.ROUTE_LOCAL
            and cloud_reason
            == "possible_private_or_local_context"
        ):

            recommendation = (
                "local"
            )

            recommendation_label = (
                "LOCAL"
            )

            reason = (
                "the request may contain local "
                "or private context"
            )

        # ---------------------------------
        # EXPLICIT CLOUD
        # ---------------------------------

        elif cloud_route == (
            CloudRoutingPolicy
            .ROUTE_CLOUD
        ):

            recommendation = (
                "cloud"
            )

            recommendation_label = (
                "CLOUD"
            )

            reason = (
                "cloud was explicitly requested"
            )

        # ---------------------------------
        # CLOUD MAY HELP
        # ---------------------------------

        elif (
            cloud_route
            == CloudRoutingPolicy.ROUTE_SUGGEST_CLOUD
        ):

            recommendation = (
                "cloud_may_help"
            )

            recommendation_label = (
                "CLOUD MAY HELP"
            )

            reason = (
                "the request may benefit from "
                "stronger cloud reasoning"
            )

        # ---------------------------------
        # NO LOCAL MODEL
        # ---------------------------------

        elif not local_success:

            recommendation = (
                "cloud_may_help"
            )

            recommendation_label = (
                "CLOUD MAY HELP"
            )

            reason = (
                "no suitable local model "
                "was detected"
            )

        # ---------------------------------
        # LOCAL SMART
        # ---------------------------------

        elif local_tier == "smart":

            recommendation = (
                "local_smart"
            )

            recommendation_label = (
                "LOCAL SMART"
            )

            reason = (
                "a capable smart-tier local model "
                "is available, so the request can "
                "stay private"
            )

        # ---------------------------------
        # LOCAL HEAVY
        # ---------------------------------

        elif local_tier == "heavy":

            recommendation = (
                "local_heavy"
            )

            recommendation_label = (
                "LOCAL HEAVY"
            )

            reason = (
                "a heavy local model was selected "
                "and cloud is not required"
            )

        # ---------------------------------
        # LOCAL FAST
        # ---------------------------------

        else:

            recommendation = (
                "local_fast"
            )

            recommendation_label = (
                "LOCAL FAST"
            )

            reason = (
                "a fast local model is sufficient "
                "for this request"
            )

        return {
            "recommendation": (
                recommendation
            ),
            "recommendation_label": (
                recommendation_label
            ),
            "reason": reason,
            "complexity_score": (
                complexity
            ),

            "local": {
                "available": (
                    local_success
                ),
                "model": (
                    local_model
                ),
                "tier": (
                    local_tier
                ),
                "private": True,
                "internet_required": False,
                "installed_models": (
                    list(
                        installed_models
                    )
                )
            },

            "cloud": {
                "route": (
                    cloud_route
                ),
                "explicit_cloud": (
                    bool(
                        cloud_decision.get(
                            "explicit_cloud"
                        )
                    )
                ),
                "authorized": False,
                "internet_required": True,
                "requires_permission": True,
                "benefit": (
                    cloud_benefit.get(
                        "level"
                    )
                ),
                "benefit_reason": (
                    cloud_benefit.get(
                        "reason"
                    )
                )
            },

            "fallback": {
                "local_model": (
                    local_model
                ),
                "local_tier": (
                    local_tier
                )
            },

            "action_taken": (
                "none"
            )
        }