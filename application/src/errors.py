class ValidationError(Exception):
    """This exception is raised in case of validation failures"""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
