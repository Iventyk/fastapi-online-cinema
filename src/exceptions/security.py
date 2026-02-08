class TokenExpiredError(Exception):
    """Exception raised when a token is expired"""

    pass


class InvalidTokenError(Exception):
    """Exception raised when a token is invalid"""

    pass


class PasswordChangeError(Exception):
    """Exception raised when a password is incorrect"""

    pass
