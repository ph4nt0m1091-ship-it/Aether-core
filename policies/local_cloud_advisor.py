from model_router import (
    ModelRouter
)

from policies.cloud_routing_policy import (
    CloudRoutingPolicy
)


class LocalCloudAdvisor:
    """
    Advisory comparison between Aether's
    local Ollama path and cloud path.

    This class NEVER executes a model.

    It only recommends:
    - local
    - cloud may help
    - cloud blocked

    Local model recommendations are produced
    using Aether's existing ModelRouter.
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

        cloud_route = (
            cloud_decision.get(
                "route",
                "local"
            )
        )

        # ---------------------------------
        # CLOUD BLOCKED
        # ---------------------------------

        if cloud_route == (
            CloudRoutingPolicy
            .ROUTE_BLOCK_CLOUD
        ):

            recommendation = (
                "local"
            )

            reason = (
                "cloud is blocked because the "
                "request may contain a secret "
                "or credential"
            )

        # ---------------------------------
        # PRIVATE / LOCAL CONTEXT
        # ---------------------------------

        elif (
            cloud_route
            == CloudRoutingPolicy.ROUTE_LOCAL
            and cloud_decision.get(
                "reason"
            )
            == "possible_private_or_local_context"
        ):

            recommendation = (
                "local"
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

            reason = (
                "cloud was explicitly requested"
            )

        # ---------------------------------
        # CLOUD MAY HELP
        # ---------------------------------

        elif cloud_route == (
            CloudRoutingPolicy
            .ROUTE_SUGGEST_CLOUD
        ):

            recommendation = (
                "cloud_may_help"
            )

            reason = (
                "the request may benefit from "
                "stronger cloud reasoning"
            )

        # ---------------------------------
        # DEFAULT LOCAL
        # ---------------------------------

        else:

            recommendation = (
                "local"
            )

            reason = (
                "local execution is Aether's "
                "default"
            )

        # ---------------------------------
        # LOCAL MODEL INFO
        # ---------------------------------

        if local_decision.get(
            "success"
        ):

            local_model = (
                local_decision.get(
                    "model"
                )
            )

            local_tier = (
                local_decision.get(
                    "tier"
                )
            )

        else:

            local_model = None
            local_tier = None

        return {
            "recommendation": (
                recommendation
            ),
            "reason": reason,

            "local": {
                "available": bool(
                    local_decision.get(
                        "success"
                    )
                ),
                "model": (
                    local_model
                ),
                "tier": (
                    local_tier
                ),
                "private": True,
                "internet_required": False
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
                "requires_permission": True
            },

            "action_taken": (
                "none"
            )
        }