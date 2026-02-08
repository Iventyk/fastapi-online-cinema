from src.exceptions.accounts import (
    BaseAccountException,
    UserAlreadyExist,
    UserGroupNotExist,
    UserNotExist,
    IncorrectCredentials,
    UserAccountNotActivated,
    UserAlreadyActivated,
    UserNotActivated,
    UserPermissionDenied,
)
from src.exceptions.shopping_cart import (
    CartItemAlreadyExist,
    CartItemDoesNotExist,
    CartItemsDoesNotExist,
)
from src.exceptions.movies import (
    MovieDoesNotExist,
)
from src.exceptions.payment import (
    RepeatPurchaseNotAllowed,
)
from src.exceptions.security import (
    TokenExpiredError,
    InvalidTokenError,
    PasswordChangeError,
)
from src.exceptions.profile import (
    ProfileAlreadyExistsException,
    ProfileDoesNotExistException,
)
from src.exceptions.storages import (
    S3PermissionError,
    S3ConnectionError,
    S3FileNotFoundError,
    S3BucketNotFoundError,
    S3FileUploadError,
    BaseS3Error,
)
from src.exceptions.email import BaseEmailError

__all__ = [
    "BaseAccountException",
    "UserAlreadyExist",
    "UserGroupNotExist",
    "TokenExpiredError",
    "InvalidTokenError",
    "UserPermissionDenied",
    "UserNotExist",
    "IncorrectCredentials",
    "UserAccountNotActivated",
    "UserAlreadyActivated",
    "UserNotActivated",
    "PasswordChangeError",
    "ProfileAlreadyExistsException",
    "ProfileDoesNotExistException",
    "MovieDoesNotExist",
    "RepeatPurchaseNotAllowed",
    "CartItemAlreadyExist",
    "CartItemDoesNotExist",
    "CartItemsDoesNotExist",
    # storage errors
    "S3PermissionError",
    "S3ConnectionError",
    "S3FileNotFoundError",
    "S3BucketNotFoundError",
    "S3FileUploadError",
    "BaseS3Error",
    # email errors
    "BaseEmailError",
]
