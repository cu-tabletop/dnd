class StartDataMissingError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self) -> str:
        if not self.message:
            return "Required start data for dialog to be initialized wasn't fully passed."
        return self.message


class StartDataInvalidError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self) -> str:
        if not self.message:
            return "Required start data for dialog to be initialized was passed in the wrong format."
        return self.message
