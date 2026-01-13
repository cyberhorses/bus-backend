from core.models import Folder, User, FolderPermission
from django.core.exceptions import ValidationError


def create_folder_for_user(name: str, owner_id: str) -> Folder:
    if not name.strip():
        raise ValidationError("Folder name cannot be empty.")

    owner = User.objects.filter(id=owner_id).first()
    if not owner:
        raise ValidationError("Invalid user ???? should never happen")

    if Folder.objects.filter(name=name, owner=owner).exists():
        raise ValidationError("A folder with this name already exists for this user.")

    folder = Folder.objects.create(name=name, owner=owner)
    FolderPermission.objects.create(folder=folder, user=owner, can_read=True, can_upload=True, can_delete=True)

    return folder


def get_available_folders(user_id: str):
    permissions = (
        FolderPermission.objects.filter(user_id=user_id, can_read=True)
        | FolderPermission.objects.filter(user_id=user_id, can_upload=True)
        | FolderPermission.objects.filter(user_id=user_id, can_delete=True)
    ).select_related("folder__owner")

    folders = [
        {
            "id": str(permission.folder.id),
            "ownerUsername": permission.folder.owner.username,
            "name": permission.folder.name,
            "permissions": {
                "read": permission.can_read,
                "upload": permission.can_upload,
                "delete": permission.can_delete,
            },
        }
        for permission in permissions
    ]

    return folders
