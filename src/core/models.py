import uuid
from django.db import models
from django.contrib import admin


class User(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    username = models.CharField(max_length=191, unique=True)
    password_hash = models.CharField(max_length=255)
    token_version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "created_at")


class RefreshToken(models.Model):
    jti = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="refresh_tokens")
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ("jti", "user", "issued_at", "revoked_at")


class Folder(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, db_column="owner_id", related_name="folders")


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner")


class File(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, db_column="folder_id", related_name="files")
    size = models.PositiveIntegerField()


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "folder", "size")


class FolderPermission(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    folder = models.ForeignKey(
        Folder, on_delete=models.CASCADE, db_column="folder_id", related_name="folder_permissions"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="folder_permissions")
    can_read = models.BooleanField(default=False)
    can_upload = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)


@admin.register(FolderPermission)
class FolderPermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "folder", "user", "can_read", "can_upload", "can_delete")
