# Authentication via JWT (migrated from session tokens)
# See: docs/Authentication - Session Token Flow (OUTDATED - needs update)
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_token(user_id: int) -> str:
    """Issues a signed JWT access token. Replaces create_session()."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Validates and decodes JWT. Replaces get_session()."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

# NOTE: create_session(), get_session(), destroy_session() removed.
# Redis session store no longer used for auth.
