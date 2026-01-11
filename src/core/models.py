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
