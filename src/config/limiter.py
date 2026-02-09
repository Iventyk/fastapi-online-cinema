from slowapi import Limiter
from slowapi.util import get_remote_address


from src.config import get_settings

settings = get_settings()

if settings.__class__.__name__ == "TestingSettings":
    storage_uri = "memory://"
else:
    storage_uri = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"

limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)
