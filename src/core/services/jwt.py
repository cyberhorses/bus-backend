from datetime import datetime, timedelta, timezone
from joserfc import jwt
from joserfc.jwk import OctKey
from joserfc.jwt import JWTClaimsRegistry
from joserfc.errors import ClaimError
from django.conf import settings
from core.models import RefreshToken
from core.services.helpers import get_user, get_user_by_uuid

key = OctKey.import_key(settings.JWT_SECRET)


def create_access_token(username: str) -> str:
    user = get_user(username)
    if user is None:
        raise ValueError("user not found")

    now = datetime.now(tz=timezone.utc)

    claims = {
        "iss": settings.JWT_ISSUER,
        "sub": str(user.id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXP_MINUTES),
        "tkv": str(user.token_version)
    }

    jwt.check_sensitive_data(claims)

    token = jwt.encode(
        header={"alg": "HS256"},
        claims=claims,
        key=key,
    )

    return token

def validate_jwt(token: str) -> bool:
    token_decoded = jwt.decode(token, key)
    user = get_user_by_uuid(token_decoded.claims["sub"])
    if user is None:
        return False

    claims_requests = JWTClaimsRegistry(
        iss={"essential": True, "value": settings.JWT_ISSUER},
        tkv={"essential": True, "value": str(user.token_version)}
    )

    try:
        claims_requests.validate(token_decoded.claims)
    except Exception:
        return False
    return True

def decode_user_uuid(token: str) -> str:
    token_decoded = jwt.decode(token, key)
    return token_decoded.claims["sub"]


def create_refresh_token(username: str) -> str:
    user = get_user(username)
    if user is None:
        raise ValueError("user not found")

    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(minutes=settings.JWT_REFRESH_EXP_MINUTES)

    token = RefreshToken.objects.create(
        user=user,
        issued_at=now,
        expires_at=exp,
        revoked_at=None,
    )

    claims = {
        "iss": settings.JWT_ISSUER,
        "sub": str(user.id),
        "jti": str(token.jti),
        "iat": now,
        "exp": exp,
    }

    jwt.check_sensitive_data(claims)

    token = jwt.encode(
        header={"alg": "HS256"},
        claims=claims,
        key=key,
    )

    return token

def decode_token_jti(token: str) -> str:
    token_decoded = jwt.decode(token, key)
    jti = token_decoded.claims["jti"]
    if not jti:
        raise ValueError("JWT not found in database")
    return str(jti)


def expire_refresh_token(token: str):
    jti = decode_token_jti(token)
    RefreshToken.objects.filter(jti=jti).update(revoked_at=datetime.now(tz=timezone.utc))


def validate_refresh_jwt(token: str) -> bool:
    token_decoded = jwt.decode(token, key)
    jti = token_decoded.claims["jti"]
    token_db = RefreshToken.objects.filter(jti=jti).first()
    if token_db is None or token_db.revoked_at is not None:
        return False

    claims_requests = JWTClaimsRegistry(
        iss={"essential": True, "value": settings.JWT_ISSUER},
    )

    try:
        claims_requests.validate(token_decoded.claims)
    except ClaimError as error:
        print(error.claim, error.error, error.description)
        return False
    return True

def get_user_from_refresh_token(token: str):
    jti = decode_token_jti(token)
    token_db = RefreshToken.objects.filter(jti=jti).first()
    return token_db.user if token_db else None

