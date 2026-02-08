class BaseMovieException(Exception):

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "Something went wrong during movie operation"
        super().__init__(message)


class MovieDoesNotExist(BaseMovieException):
    pass


class MovieAlreadyPurchased(BaseMovieException):
    pass
