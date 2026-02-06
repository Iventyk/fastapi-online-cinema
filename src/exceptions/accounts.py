class BaseAccountException(Exception):

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "Something went wrong during account operation"
        super().__init__(message)


class UserAlreadyExist(BaseAccountException):
    pass


class UserNotExist(BaseAccountException):
    pass


class UserGroupNotExist(BaseAccountException):
    pass


class IncorrectCredentials(BaseAccountException):
    pass


class UserPermissionDenied(BaseAccountException):
    pass