from init_data_py import validate_by_hash

from backend.app.modules.auth.dto.user_identity import (
    AuthProvider,
    UserIdentityDTO,
)


class TelegramProvider:
    def __init__(self, bot_token: str, max_auth_age: int):
        self._bot_token = bot_token
        self._max_auth_age = max_auth_age

    def authenticate(self, init_data: str) -> UserIdentityDTO:
        result = validate_by_hash(
            init_data=init_data,
            bot_token=self._bot_token,
            expires_in=self._max_auth_age,
        )
        return UserIdentityDTO(
            provider=AuthProvider.TELEGRAM,
            external_id=result.user.id,
            first_name=result.user.first_name,
            last_name=result.user.last_name,
            username=result.user.username,
            avatar_url=result.user.photo_url,
            locale=result.user.language_code,
        )
