from fastapi import FastAPI

from backend.app.core.exceptions import AppException
from backend.app.core.handler import app_exception_handler
from backend.app.modules.auth.api.auth_router import auth_router
from backend.app.modules.user.api.user_router import user_router


def create_app() -> FastAPI:
    """Create the HTTP application and register its public modules."""
    app = FastAPI()
    app.add_exception_handler(AppException, app_exception_handler)
    app.include_router(auth_router)
    app.include_router(user_router)
    return app


app = create_app()
