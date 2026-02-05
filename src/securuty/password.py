import bcrypt
from typing import cast


def hash_password(password: str) -> str:

    pwd_bytes = password.encode("utf-8")

    salt = bcrypt.gensalt()
    hashed = cast(bytes, bcrypt.hashpw(pwd_bytes, salt))

    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:

    try:
        return cast(bool, bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        ))
    except Exception:
        return False
