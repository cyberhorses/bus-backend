import uuid
from django.db import models

class User(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)  # UUID in binary
    username = models.CharField(max_length=191, unique=True)
    password_hash = models.CharField(max_length=255)
    token_version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().bytes
        super().save(*args, **kwargs)
