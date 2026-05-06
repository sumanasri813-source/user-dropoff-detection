from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.utils.auth import load_jwt_config


def _get_serializer() -> URLSafeTimedSerializer:
    secret_key, _, _ = load_jwt_config()
    return URLSafeTimedSerializer(secret_key)


def generate_csrf_token() -> str:
    s = _get_serializer()
    return s.dumps({"csrf": True})


def validate_csrf_token(token: str, max_age: int = 3600) -> bool:
    s = _get_serializer()
    try:
        data = s.loads(token, max_age=max_age)
        return isinstance(data, dict) and data.get("csrf") is True
    except (BadSignature, SignatureExpired):
        return False
