from typing import Optional
from uuid import UUID
from core.models import User
from django.db.models import F


def get_user(username: str) -> Optional[User]:
    user = User.objects.filter(username=username).first()
    return user if user else None


def get_user_by_uuid(id: str) -> Optional[User]:
    user = User.objects.filter(id=id).first()
    return user if user else None


def increment_token_version(id: str) -> None:
    User.objects.filter(id=id).update(token_version=F('token_version') + 1)

