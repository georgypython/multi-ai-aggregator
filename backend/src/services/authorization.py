from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Literal
import hashlib
import hmac
import json
from urllib.parse import parse_qsl

import jwt
from fastapi import Response

from src.schemas.authorization import TokenData, TokenPayload, TokenType
from src.schemas.telegram_account import TelegramUser
from src.exceptions.tg import InitDataValidationError


class AuthorizationService:
    def __init__(
        self,
        tg_bot_token: str,
        access_secret: str,
        refresh_secret: str,
        algorithm: str,
        access_ttl_minutes: int,
        refresh_ttl_days: int,
        cookie_secure: bool,
        cookie_httponly: bool,
        cookie_samesite: Literal["lax", "strict", "none"],
        cookie_domain: str | None,
    ) -> None:
        self._tg_bot_token = tg_bot_token
        self._access_secret = access_secret
        self._refresh_secret = refresh_secret
        self._algorithm = algorithm
        self._access_ttl_minutes = access_ttl_minutes
        self._refresh_ttl_days = refresh_ttl_days
        self._cookie_secure = cookie_secure
        self._cookie_httponly = cookie_httponly
        self._cookie_samesite = cookie_samesite
        self._cookie_domain = cookie_domain

    def verify_init_data(self, init_data: str) -> TelegramUser:
        params = dict(parse_qsl(init_data))
        received_hash = params.pop("hash", None)
        if not received_hash:
            raise InitDataValidationError

        raw_user = params.get("user")
        if not raw_user:
            raise InitDataValidationError

        sorted_items = sorted(params.items())
        data_check_string = "\n".join(f"{key}={value}" for key, value in sorted_items)
        secret_key = hmac.new(
            b"WebAppData", self._tg_bot_token.encode(), hashlib.sha256
        ).digest()
        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            raise InitDataValidationError

        return TelegramUser(**json.loads(raw_user))

    def _encode_token(self, token_type: TokenType, data: TokenData) -> str:
        now = datetime.now(timezone.utc)
        ttl = (
            timedelta(minutes=self._access_ttl_minutes)
            if token_type is TokenType.ACCESS
            else timedelta(days=self._refresh_ttl_days)
        )
        payload = {
            "user_id": str(data.user_id),
            "scope": data.scope,
            "token_type": token_type.value,
            "iat": int(now.timestamp()),
            "exp": int((now + ttl).timestamp()),
        }
        secret = (
            self._access_secret
            if token_type is TokenType.ACCESS
            else self._refresh_secret
        )
        return jwt.encode(payload, secret, algorithm=self._algorithm)

    def verify_token(self, token: str, token_type: TokenType) -> TokenPayload:
        secret = (
            self._access_secret
            if token_type == TokenType.ACCESS
            else self._refresh_secret
        )
        payload = jwt.decode(token, secret, algorithms=[self._algorithm])

        if payload.get("token_type") != token_type.value:
            raise jwt.InvalidTokenError

        try:
            user_id = UUID(str(payload["user_id"]))
        except (KeyError, ValueError):
            raise jwt.InvalidTokenError

        scope = str(payload.get("scope") or "")
        if not scope:
            raise jwt.InvalidTokenError

        return TokenPayload(user_id=user_id, scope=scope, token_type=token_type)

    def set_auth_cookies(self, response: Response, data: TokenData) -> None:
        access = self._encode_token(TokenType.ACCESS, data)
        refresh = self._encode_token(TokenType.REFRESH, data)
        access_expires = datetime.now(timezone.utc) + timedelta(
            minutes=self._access_ttl_minutes
        )
        refresh_expires = datetime.now(timezone.utc) + timedelta(
            days=self._refresh_ttl_days
        )

        response.set_cookie(
            key="access_token",
            value=access,
            httponly=self._cookie_httponly,
            secure=self._cookie_secure,
            samesite=self._cookie_samesite,
            domain=self._cookie_domain,
            expires=access_expires,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=self._cookie_httponly,
            secure=self._cookie_secure,
            samesite=self._cookie_samesite,
            domain=self._cookie_domain,
            expires=refresh_expires,
        )

    def clear_auth_cookies(self, response: Response) -> None:
        response.delete_cookie(
            key="access_token",
            domain=self._cookie_domain,
            secure=self._cookie_secure,
            httponly=self._cookie_httponly,
            samesite=self._cookie_samesite,
        )
        response.delete_cookie(
            key="refresh_token",
            domain=self._cookie_domain,
            secure=self._cookie_secure,
            httponly=self._cookie_httponly,
            samesite=self._cookie_samesite,
        )
