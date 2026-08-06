from tools.calculator_tool import CalculatorTool


class CalculatorSkill:

    def __init__(self, memory):
        self.memory = memory
        self.calculator = CalculatorTool()

    def handle(self, message):

        message = message.lower().strip()

        prefixes = [
            "calculate ",
            "what is ",
            "what's "
        ]

        expression = None

        for prefix in prefixes:

            if message.startswith(prefix):

                expression = message[len(prefix):]

                break

        if expression is None:
            return None

        expression = expression.replace("^", "**")

        result = self.calculator.calculate(expression)

        if result is None:
            return "Aether: I couldn't calculate that."

        return f"Aether: The answer is {result}."