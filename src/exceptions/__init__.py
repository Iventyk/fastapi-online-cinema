from src.exceptions.accounts import (
    BaseAccountException,
    UserAlreadyExist,
    UserGroupNotExist,
    UserNotExist,
    UserPermissionDenied,
    IncorrectCredentials,
)
from src.exceptions.shopping_cart import (
    CartItemAlreadyExist,
    CartItemDoesNotExist,
    CartItemsDoesNotExist,
)
from src.exceptions.movies import (
    MovieDoesNotExist,
    MovieAlreadyPurchased,
)
from src.exceptions.security import (
    TokenExpiredError,
    InvalidTokenError,
)
from src.exceptions.payment import (
    RepeatPurchaseNotAllowed,
)
from src.exceptions.orders import (
    OrderNotFound,
    OrderCancellationNotPossible,
    PendingOrderExists,
    OrderAlreadyPaid,
)

__all__ = [
    "BaseAccountException",
    "UserAlreadyExist",
    "UserGroupNotExist",
    "UserNotExist",
    "UserPermissionDenied",
    "IncorrectCredentials",
    "TokenExpiredError",
    "InvalidTokenError",
    "CartItemAlreadyExist",
    "CartItemDoesNotExist",
    "MovieDoesNotExist",
    "MovieAlreadyPurchased",
    "RepeatPurchaseNotAllowed",
    "CartItemsDoesNotExist",
    "OrderNotFound",
    "OrderCancellationNotPossible",
    "PendingOrderExists",
    "OrderAlreadyPaid",
]
