from providers.invocation_adapters.hermes_adapter import (
    HermesInvocationAdapter
)


class InvocationAdapterRegistry:
    """
    Stores provider-specific invocation adapters.

    Agent routing decides WHO should perform a task.

    Invocation adapters decide HOW that worker
    should be invoked.
    """

    def __init__(
        self
    ):

        self.adapters = {}

        self.register(
            HermesInvocationAdapter()
        )

    # ---------------------------------
    # REGISTER
    # ---------------------------------

    def register(
        self,
        adapter
    ):

        if adapter is None:

            return False

        provider_name = getattr(
            adapter,
            "provider_name",
            None
        )

        if not provider_name:

            return False

        self.adapters[
            str(
                provider_name
            ).strip().lower()
        ] = adapter

        return True

    # ---------------------------------
    # GET
    # ---------------------------------

    def get(
        self,
        provider_name
    ):

        if not provider_name:

            return None

        return self.adapters.get(
            str(
                provider_name
            ).strip().lower()
        )

    # ---------------------------------
    # BUILD
    # ---------------------------------

    def build(
        self,
        provider_name,
        task,
        role=None,
        options=None
    ):

        adapter = self.get(
            provider_name
        )

        if adapter is None:

            return {
                "success": False,
                "provider": (
                    provider_name
                ),
                "status": (
                    "adapter_not_found"
                ),
                "error": (
                    "No invocation adapter "
                    f'is registered for "{provider_name}".'
                )
            }

        result = adapter.build(
            task=task,
            role=role,
            options=options
        )

        if isinstance(
            result,
            dict
        ):

            result.setdefault(
                "status",
                (
                    "built"
                    if result.get(
                        "success"
                    )
                    else "build_failed"
                )
            )

        return result

    # ---------------------------------
    # INFO
    # ---------------------------------

    def info(
        self
    ):

        return [
            adapter.info()
            for adapter in (
                self.adapters.values()
            )
        ]