class BaseOrderException(Exception):

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "Something went wrong during order operation"
        super().__init__(message)


class OrderNotFound(BaseOrderException):
    pass


class OrderCancellationNotPossible(BaseOrderException):
    pass


class PendingOrderExists(BaseOrderException):
    pass


class OrderAlreadyPaid(BaseOrderException):
    pass
