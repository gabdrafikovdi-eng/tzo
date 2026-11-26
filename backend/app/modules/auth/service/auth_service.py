from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.modules.auth.dto.auth_result import AuthResultDTO
from backend.app.modules.auth.providers.telegram import TelegramProvider
from backend.app.modules.auth.service.identity_service import IdentityService
from backend.app.modules.auth.service.session_service import SessionService
from backend.app.modules.auth.service.token_service import TokenService


class AuthService:
    def __init__(self, session: AsyncSession):
        self._settings = get_settings()
        self._token_service = TokenService()
        self._telegram = TelegramProvider(
            bot_token=self._settings.TELEGRAM_BOT,
            max_auth_age=self._settings.TELEGRAM_INIT_DATA_EXPIRES,
        )
        self._identity_service = IdentityService(session=session)
        self._session_service = SessionService(session=session)

    async def authenticate_telegram(self, init_data: str) -> AuthResultDTO:
        user_identity = self._telegram.authenticate(init_data=init_data)

        resolved = await self._identity_service.resolve(identity=user_identity)

        refresh_token = self._token_service.create_refresh_token()
        user_session = await self._session_service.create_session(
            user_id=resolved.user.id, refresh_token=refresh_token
        )
        access_token = self._token_service.create_access_token(
            user_id=resolved.user.id, session_id=user_session.id
        )

        return AuthResultDTO(
            user=resolved.user, access_token=access_token, refresh_token=refresh_token
        )
