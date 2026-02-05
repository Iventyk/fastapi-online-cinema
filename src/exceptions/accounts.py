class BaseAccountException(Exception):

    def __init__(self, message=None):
        if message is None:
            message = "Something went wrong during account operation"
        super().__init__(message)


class UserAlreadyExist(BaseAccountException):
    pass
