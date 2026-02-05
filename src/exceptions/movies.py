class BaseMoviesException(Exception):

    def __init__(self, message: str | None = None) -> None:
        if message is None:
            message = "Something went wrong during cart operation"
        super().__init__(message)


class MovieDoesNotExist(BaseMoviesException):
    pass
