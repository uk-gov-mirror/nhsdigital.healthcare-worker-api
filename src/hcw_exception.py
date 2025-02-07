from logs.log import Log

logger = Log("hcw_exception")


class HcwException(Exception):
    status_code: int
    code: str
    return_message: str
    fhir_code: str

    def __init__(self, status_code: int, code: str | None, message: str, detail_code: str, return_message: str = None):
        super().__init__(message)

        self.status_code = status_code
        self.code = code
        self.message = message
        self.return_message = return_message
        self.fhir_code = detail_code

        if not self.return_message:
            # We might want to log more information in the exception (seen only in our logs) and the message we
            # return to the caller. If only one message is specified then we use it for both.
            self.return_message = message
