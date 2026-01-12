from typing import Optional
from uuid import UUID
from core.models import User, Folder, File, FolderPermission
from django.db.models import F


def get_user(username: str) -> Optional[User]:
    user = User.objects.filter(username=username).first()
    return user if user else None


def get_user_by_uuid(id: str) -> Optional[User]:
    user = User.objects.filter(id=id).first()
    return user if user else None


def increment_token_version(id: str) -> None:
    User.objects.filter(id=id).update(token_version=F('token_version') + 1)


def get_folder_by_uuid(id: str) -> Optional[Folder]:
    folder = Folder.objects.filter(id=id).first()
    return folder if folder else None


def get_user_folder_permissions(folder: Folder, user: User) -> list[str]:
    permission = FolderPermission.objects.filter(folder=folder, user=user).first()
    perms = []
    if not permission: return perms
    if permission.can_read: perms.append("read")
    if permission.can_upload: perms.append("upload")
    if permission.can_delete: perms.append("delete")
    return perms


def get_file_by_uuid(id: str) -> Optional[File]:
    file = File.objects.filter(id=id).first()
    return file if file else None
