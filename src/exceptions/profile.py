class ProfileBaseException(Exception):
    """Base exception for all exceptions raised by this module."""

    def __init__(self, message: str):
        if message is None:
            message = "Something went wrong during profile operation"
        super().__init__(message)


class ProfileAlreadyExistsException(ProfileBaseException):
    pass


class ProfileDoesNotExistException(ProfileBaseException):
    pass
