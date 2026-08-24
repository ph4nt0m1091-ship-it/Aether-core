from tools.calculator_tool import CalculatorTool


class CalculatorSkill:
    """
    Handles calculator requests.

    Natural-language questions such as:
        what is the difference between RAM and storage

    are ignored unless the content actually looks
    like a mathematical expression.
    """

    name = "calculator"

    description = (
        "Performs mathematical calculations."
    )

    def __init__(self, memory):

        self.memory = memory
        self.calculator = CalculatorTool()

    # ---------------------------------
    # MATH REQUEST DETECTION
    # ---------------------------------

    def _looks_like_math(
        self,
        expression
    ):

        expression = str(
            expression or ""
        ).strip()

        if not expression:

            return False

        compact = (
            expression
            .replace(
                " ",
                ""
            )
        )

        # A mathematical request should contain
        # at least one digit.
        if not any(
            char.isdigit()
            for char in compact
        ):

            return False

        allowed = set(
            "0123456789"
            "+-*/%^().,"
        )

        return all(
            char in allowed
            for char in compact
        )

    # ---------------------------------
    # HANDLE
    # ---------------------------------

    def handle(
        self,
        message
    ):

        original = str(
            message or ""
        ).strip()

        lower = (
            original.lower()
        )

        prefixes = (
            "calculate ",
            "what is ",
            "what's "
        )

        expression = None
        matched_prefix = None

        for prefix in prefixes:

            if lower.startswith(
                prefix
            ):

                expression = (
                    original[
                        len(prefix):
                    ]
                    .strip()
                )

                matched_prefix = (
                    prefix
                )

                break

        if expression is None:

            return None

        # "calculate ..." is explicitly intended
        # for the calculator, so let the tool attempt
        # it even if the expression is malformed.
        #
        # Generic "what is ..." questions are only
        # claimed if they actually look mathematical.
        if (
            matched_prefix
            != "calculate "
            and not self._looks_like_math(
                expression
            )
        ):

            return None

        expression = (
            expression.replace(
                "^",
                "**"
            )
        )

        result = (
            self.calculator.calculate(
                expression
            )
        )

        if result is None:

            return (
                "Aether: I couldn't calculate that."
            )

        return (
            f"Aether: The answer is {result}."
        )

    def execute(
        self,
        step
    ):
        """
        CalculatorSkill is not used by missions.
        """

        return None
