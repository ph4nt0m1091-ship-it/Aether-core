class CalculatorTool:

    def calculate(self, expression):

        try:

            allowed = {
                "__builtins__": None
            }

            result = eval(expression, allowed, {})

            return result

        except Exception:

            return None