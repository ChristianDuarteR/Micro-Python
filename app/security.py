from typing import Any

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer(
    auto_error=False,
    bearerFormat="JWT",
    scheme_name="BearerJWT",
    description="JWT emitido por el micro Java. Claim `role` = ROLE_AUDITOR o ROLE_OPERADOR.",
)
internal_key_header = APIKeyHeader(
    name="X-Internal-Key",
    auto_error=False,
    scheme_name="InternalKey",
    description="Clave compartida Java ↔ Python (INTERNAL_API_KEY).",
)

AUDITOR_ROLE = "ROLE_AUDITOR"


def decode_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT inválido o expirado",
        ) from exc


def extract_roles(payload: dict[str, Any], settings: Settings) -> set[str]:
    claim = settings.jwt_role_claim
    raw = payload.get(claim, payload.get("roles", payload.get("authorities")))
    if raw is None:
        return set()
    if isinstance(raw, str):
        return {raw.upper()}
    if isinstance(raw, list):
        return {str(item).upper() for item in raw}
    return set()


def require_auditor(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere Bearer token",
        )
    payload = decode_token(credentials.credentials, settings)
    roles = extract_roles(payload, settings)
    if AUDITOR_ROLE not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El Dashboard de métricas es exclusivo del rol ROLE_AUDITOR",
        )
    return payload


def require_internal_key(
    x_internal_key: str | None = Security(internal_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    if not x_internal_key or x_internal_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave interna inválida",
        )
