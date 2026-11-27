from fastapi import status

from backend.app.core.exceptions import AppException


class SessionNotFoundError(AppException):
    def __init__(self, message: str = "Сессия не найдена"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SESSION_NOT_FOUND",
        )


class SessionRevokedError(AppException):
    def __init__(self, message: str = "Сессия отозвана"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="SESSION_REVOKED",
        )


class SessionExpiredError(AppException):
    def __init__(self, message: str = "Сессия истекла"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="SESSION_EXPIRED",
        )


class RefreshTokenReplayError(AppException):
    def __init__(
        self, message: str = "Обнаружено повторное использование refresh-токена"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="REFRESH_TOKEN_REPLAY",
        )


class InvalidRefreshTokenError(AppException):
    def __init__(
        self, message: str = "Недействительный refresh-токен"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_REFRESH_TOKEN",
        )


class UnknownRefreshTokenError(AppException):
    def __init__(
        self, message: str = "Refresh-токен не найден"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNKNOWN_REFRESH_TOKEN",
        )


class InactiveUserError(AppException):
    def __init__(
        self, message: str = "Пользователь заблокирован"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="INACTIVE_USER",
        )


class InvalidAccessTokenError(AppException):
    def __init__(
        self, message: str = "Недействительный access-токен"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_ACCESS_TOKEN",
        )


class UserNotFoundError(AppException):
    def __init__(
        self, message: str = "Пользователь не найден"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="USER_NOT_FOUND",
        )


class LastIdentityError(AppException):
    def __init__(
        self, message: str = "Нельзя отвязать последний способ входа"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="LAST_IDENTITY",
        )


class IdentityDeleteError(AppException):
    def __init__(
        self, message: str = "Не удалось удалить идентичность"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="IDENTITY_DELETE_ERROR",
        )


class IdentityAlreadyLinkedError(AppException):
    def __init__(
        self, message: str = "Эта identity уже привязана к другому пользователю"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="IDENTITY_ALREADY_LINKED",
        )
