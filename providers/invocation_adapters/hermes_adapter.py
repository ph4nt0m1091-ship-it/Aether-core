import shutil

from providers.invocation_adapters.base_adapter import (
    BaseInvocationAdapter
)


class HermesInvocationAdapter(
    BaseInvocationAdapter
):
    """
    Builds controlled Hermes Agent invocations.

    Hermes documentation inspected on this
    installation confirms:

        hermes chat -q "prompt"

    is the supported single-query interface.

    IMPORTANT:
    Aether deliberately does NOT use:

        hermes -z / --oneshot

    because Hermes documents that mode as
    automatically bypassing approval prompts.

    v1 only builds and previews commands.
    Execution remains disabled until Aether's
    permission bridge is explicitly tested.
    """

    name = "hermes"
    provider_name = "hermes"

    SUPPORTED_ROLES = {
        "general_agent",
        "research",
        "automation"
    }

    DEFAULT_MAX_TURNS = 25

    def __init__(
        self,
        executable="hermes"
    ):

        self.executable = (
            executable
        )

    # ---------------------------------
    # AVAILABLE
    # ---------------------------------

    def available(
        self
    ):

        return (
            shutil.which(
                self.executable
            )
            is not None
        )

    # ---------------------------------
    # EXECUTABLE PATH
    # ---------------------------------

    def executable_path(
        self
    ):

        return shutil.which(
            self.executable
        )

    # ---------------------------------
    # SUPPORTS ROLE
    # ---------------------------------

    def supports_role(
        self,
        role
    ):

        role = str(
            role or ""
        ).strip().lower()

        return (
            role
            in self.SUPPORTED_ROLES
        )

    # ---------------------------------
    # BUILD
    # ---------------------------------

    def build(
        self,
        task,
        role=None,
        options=None
    ):

        task = str(
            task or ""
        ).strip()

        role = str(
            role or "general_agent"
        ).strip().lower()

        options = (
            options
            if isinstance(
                options,
                dict
            )
            else {}
        )

        if not task:

            return {
                "success": False,
                "adapter": self.name,
                "provider": (
                    self.provider_name
                ),
                "error": (
                    "No Hermes task "
                    "was provided."
                )
            }

        if not self.available():

            return {
                "success": False,
                "adapter": self.name,
                "provider": (
                    self.provider_name
                ),
                "error": (
                    "Hermes is not installed "
                    "or is not available on PATH."
                )
            }

        if not self.supports_role(
            role
        ):

            return {
                "success": False,
                "adapter": self.name,
                "provider": (
                    self.provider_name
                ),
                "role": role,
                "error": (
                    "The Hermes adapter does not "
                    f'support role "{role}".'
                )
            }

        max_turns = options.get(
            "max_turns",
            self.DEFAULT_MAX_TURNS
        )

        try:

            max_turns = int(
                max_turns
            )

        except (
            TypeError,
            ValueError
        ):

            max_turns = (
                self.DEFAULT_MAX_TURNS
            )

        max_turns = max(
            1,
            min(
                max_turns,
                100
            )
        )

        command = [
            self.executable,
            "chat",
            "-q",
            task,
            "-Q",
            "--source",
            "tool",
            "--max-turns",
            str(
                max_turns
            )
        ]

        # ---------------------------------
        # OPTIONAL WORKTREE
        # ---------------------------------

        if options.get(
            "worktree",
            False
        ):

            command.append(
                "--worktree"
            )

        # ---------------------------------
        # OPTIONAL CHECKPOINTS
        # ---------------------------------

        if options.get(
            "checkpoints",
            False
        ):

            command.append(
                "--checkpoints"
            )

        # ---------------------------------
        # OPTIONAL TOOLSETS
        # ---------------------------------

        toolsets = options.get(
            "toolsets"
        )

        if toolsets:

            if isinstance(
                toolsets,
                (list, tuple)
            ):

                toolsets = ",".join(
                    str(item).strip()
                    for item in toolsets
                    if str(item).strip()
                )

            else:

                toolsets = str(
                    toolsets
                ).strip()

            if toolsets:

                command.extend(
                    [
                        "--toolsets",
                        toolsets
                    ]
                )

        return {
            "success": True,
            "adapter": self.name,
            "provider": (
                self.provider_name
            ),
            "provider_type": (
                "external_agent"
            ),
            "role": role,
            "task": task,
            "command": command,
            "executable": (
                self.executable
            ),
            "executable_path": (
                self.executable_path()
            ),
            "requires_permission": True,

            # ---------------------------------
            # DELIBERATE SAFETY BOUNDARY
            # ---------------------------------

            "execution_ready": False,

            "execution_block_reason": (
                "Hermes natural-task execution "
                "has not yet passed Aether's "
                "permission-bridge safety test."
            ),

            "safety": {
                "uses_shell": False,
                "uses_oneshot": False,
                "uses_yolo": False,
                "accept_hooks": False,
                "permission_bypass": False
            }
        }

    # ---------------------------------
    # INFO
    # ---------------------------------

    def info(
        self
    ):

        return {
            "name": self.name,
            "provider": (
                self.provider_name
            ),
            "available": (
                self.available()
            ),
            "executable": (
                self.executable
            ),
            "executable_path": (
                self.executable_path()
            ),
            "supported_roles": sorted(
                self.SUPPORTED_ROLES
            ),
            "execution_ready": False,
            "interface": (
                "hermes chat -q"
            ),
            "forbidden_modes": [
                "--oneshot",
                "-z",
                "--yolo",
                "--accept-hooks"
            ]
        }