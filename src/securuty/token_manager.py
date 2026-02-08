import os
from datetime import datetime, timedelta, timezone
from typing import Optional, cast, Any

from jose import jwt, JWTError, ExpiredSignatureError

from src.exceptions import TokenExpiredError, InvalidTokenError
from src.securuty import JWTAuthManagerInterface


class JWTAuthManager(JWTAuthManagerInterface):
    """
    A manager for creating, decoding, and verifying JWT access
    and refresh tokens.
    """

    _ACCESS_KEY_TIMEDELTA_MINUTES = 60
    _REFRESH_KEY_TIMEDELTA_MINUTES = 60 * 24 * 7

    def __init__(
        self, secret_key_access: str, secret_key_refresh: str, algorithm: str
    ):
        """
        Initialize the manager with secret keys and algorithm for token
        operations.
        """
        self._secret_key_access = secret_key_access
        self._secret_key_refresh = secret_key_refresh
        self._algorithm = algorithm

    def _create_token(
        self,
        data: dict[str, object],
        secret_key: str,
        expires_delta: timedelta,
    ) -> str:
        """
        Create a JWT token with provided data, secret key, and expiration time.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, secret_key, algorithm=self._algorithm
        )
        return cast(str, encoded_jwt)

    @staticmethod
    def create_activation_token() -> str:
        return os.urandom(32).hex()

    @staticmethod
    def create_reset_token() -> str:
        return os.urandom(32).hex()

    def create_access_token(
        self,
        data: dict[str, object],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a new access token with a default or specified expiration time.
        """
        return self._create_token(
            data,
            self._secret_key_access,
            expires_delta
            or timedelta(minutes=self._ACCESS_KEY_TIMEDELTA_MINUTES),
        )

    def create_refresh_token(
        self,
        data: dict[str, object],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a new refresh token with a default or specified expiration time.
        """
        return self._create_token(
            data,
            self._secret_key_refresh,
            expires_delta
            or timedelta(minutes=self._REFRESH_KEY_TIMEDELTA_MINUTES),
        )

    def decode_access_token(self, token: str) -> dict[str, object]:
        """
        Decode and validate an access token, returning the token's data.
        """
        try:
            payload = jwt.decode(
                token, self._secret_key_access, algorithms=[self._algorithm]
            )
            return cast(dict[str, Any], payload)
        except ExpiredSignatureError:
            raise TokenExpiredError
        except JWTError:
            raise InvalidTokenError

    def decode_refresh_token(self, token: str) -> dict[str, object]:
        """
        Decode and validate a refresh token, returning the token's data.
        """
        try:
            payload = jwt.decode(
                token, self._secret_key_refresh, algorithms=[self._algorithm]
            )
            return cast(dict[str, Any], payload)
        except ExpiredSignatureError:
            raise TokenExpiredError
        except JWTError:
            raise InvalidTokenError

    def verify_refresh_token_or_raise(self, token: str) -> None:
        """
        Verify a refresh token and raise an error if it's invalid or expired.
        """
        self.decode_refresh_token(token)

    def verify_access_token_or_raise(self, token: str) -> None:
        """
        Verify an access token and raise an error if it's invalid or expired.
        """
        self.decode_access_token(token)
