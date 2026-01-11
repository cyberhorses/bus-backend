from datetime import datetime, timedelta, timezone
from joserfc import jwt
from joserfc.jwk import OctKey
from joserfc.jwt import JWTClaimsRegistry
from joserfc.errors import ClaimError
from django.conf import settings
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

    print(user.token_version)
    claims_requests = JWTClaimsRegistry(
        iss={"essential": True, "value": settings.JWT_ISSUER},
        tkv={"essential": True, "value": str(user.token_version)}
    )

    try:
        claims_requests.validate(token_decoded.claims)
    except ClaimError as error:
        print(error.claim, error.error, error.description)
        return False
    return True

def decode_user_uuid(token: str) -> str:
    token_decoded = jwt.decode(token, key)
    return token_decoded.claims["sub"]

