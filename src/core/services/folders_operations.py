from core.models import Folder, User, FolderPermission
from django.core.exceptions import ValidationError


def create_folder_for_user(name: str, owner_id: str) -> Folder:
    if not name.strip():
        raise ValidationError("Folder name cannot be empty.")

    owner = User.objects.filter(id=owner_id).first()
    if not owner:
        raise ValidationError("User with the given owner_id does not exist. ???? should never happen")

    if Folder.objects.filter(name=name, owner=owner).exists():
        raise ValidationError("A folder with this name already exists for this user.")

    folder = Folder.objects.create(name=name, owner=owner)
    FolderPermission.objects.create(folder=folder, user=owner, read=True, upload=True, delete=True)

    return folder
