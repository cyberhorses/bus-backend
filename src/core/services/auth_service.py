from django.contrib.auth.hashers import check_password
from core.models import User
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password
import uuid
from typing import Optional

def verify_user_credentials(username: str, password: str):
    """
    Returns the user object if credentials are correct, else None.
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return None

    if check_password(password, user.password_hash):
        return user
    return None


def create_user(username: str, password: str) -> Optional[User]:
    """
    Creates a new user with hashed password.
    Returns the User object on success, None if username exists.
    """
    try:
        user = User(
            id=uuid.uuid4(),
            username=username,
            password_hash=make_password(password)
        )
        user.save()
        return user
    except IntegrityError:
        # Username already exists
        return None
