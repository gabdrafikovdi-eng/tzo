# Backend

## Auth MVP

The public Auth API is served by `backend.app.main:app`.

- `POST /auth/telegram` validates Telegram Mini App `init_data`, creates or
  resolves an identity, and sets the refresh-token cookie.
- `POST /auth/refresh` rotates that cookie and returns a new access JWT.
- `POST /auth/logout` revokes the current refresh-token session.
- `POST /auth/logout-all` requires `Authorization: Bearer <access token>` and
  revokes every active session for that user.

Access tokens contain `sub`, `sid`, `type`, `iat`, and `exp`.  Protected
dependencies validate the JWT and verify that the referenced session is still
active. Refresh tokens are only stored as SHA-256 hashes, rotate on use, and a
replayed token revokes the whole session.

Required environment variables are `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `JWT_SECRET_KEY`, and
`TELEGRAM_BOT` (or its legacy alias `TELEGRAM_TOKEN`). `JWT_SECRET_KEY` must
be at least 32 bytes for HS256. Set `COOKIE_SECURE=false` only in a local HTTP
development environment.

Run tests from the repository root with:

```powershell
backend\.venv\Scripts\python.exe -m pytest -q backend\tests
```

Tests use `TEST_DATABASE_URL` when supplied; otherwise they target a separate
database named `<POSTGRES_DB>-test`.
