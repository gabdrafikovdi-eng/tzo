import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from backend.app.core.config import get_settings
from backend.app.modules.auth.exceptions import InvalidAccessTokenError


class TokenService:
    def __init__(self):
        self._settings = get_settings()

    def create_access_token(self, user_id: UUID, session_id: UUID) -> str:
        now = datetime.now(UTC)

        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }

        return jwt.encode(
            payload=payload,
            algorithm=self._settings.JWT_ALGORITHM,
            key=self._settings.JWT_SECRET_KEY,
        )

    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(self._settings.NBYTES_SECRET_USER_SESSION)

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def decode_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                jwt=token,
                key=self._settings.JWT_SECRET_KEY,
                algorithms=[self._settings.JWT_ALGORITHM],
                options={
                    "require": ["sub", "sid", "type", "exp", "iat"],
                },
            )
            if payload.get("type") != "access":
                raise InvalidAccessTokenError()
            UUID(payload["sub"])
            UUID(payload["sid"])
        except InvalidAccessTokenError:
            raise
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
            raise InvalidAccessTokenError() from exc

        return payload
