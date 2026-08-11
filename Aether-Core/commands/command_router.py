class CommandRouter:
    """
    Routes user commands to specialized command handlers.
    """

    def __init__(self):

        self.handlers = []

    def register(self, handler):

        self.handlers.append(handler)

    def handle(self, brain, message):

        for handler in self.handlers:

            response = handler.handle(brain, message)

            if response is not None:

                return response

        return None