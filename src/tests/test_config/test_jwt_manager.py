import pytest
from datetime import timedelta
from src.security import JWTAuthManager
from src.security.interfaces import JWTAuthManagerInterface
from src.exceptions import TokenExpiredError, InvalidTokenError


@pytest.fixture
def jwt_manager() -> JWTAuthManagerInterface:
    return JWTAuthManager(
        secret_key_access="test_access_key",
        secret_key_refresh="test_refresh_key",
        algorithm="HS256",
    )


def test_create_and_decode_access_token(
    jwt_manager: JWTAuthManagerInterface,
) -> None:
    data = {"user_id": 1, "role": "admin"}

    token = jwt_manager.create_access_token(data=data)

    decoded_data = jwt_manager.decode_access_token(token)

    assert decoded_data["user_id"] == 1
    assert decoded_data["role"] == "admin"
    assert "exp" in decoded_data


def test_access_token_fails_with_refresh_key(
    jwt_manager: JWTAuthManagerInterface,
) -> None:
    data = {"user_id": 1}
    access_token = jwt_manager.create_access_token(data=data)  # type: ignore[arg-type]

    with pytest.raises(InvalidTokenError):
        jwt_manager.decode_refresh_token(access_token)


def test_token_expiration(jwt_manager: JWTAuthManagerInterface) -> None:
    data = {"user_id": 1}
    token = jwt_manager.create_access_token(
        data=data, expires_delta=timedelta(minutes=-1)  # type: ignore[arg-type]
    )

    with pytest.raises(TokenExpiredError):
        jwt_manager.decode_access_token(token)


def test_static_methods(jwt_manager: JWTAuthManagerInterface) -> None:
    token1 = jwt_manager.create_activation_token()
    token2 = jwt_manager.create_activation_token()

    assert len(token1) == 64
    assert token1 != token2
