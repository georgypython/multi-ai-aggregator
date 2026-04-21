from enum import StrEnum
from uuid import UUID

from dataclasses import dataclass


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(slots=True)
class TokenPayload:
    user_id: UUID
    scope: str
    token_type: TokenType


@dataclass(slots=True)
class TokenData:
    user_id: UUID
    scope: str
