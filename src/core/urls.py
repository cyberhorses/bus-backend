from django.urls import path
from . import views
from . import blob_views

urlpatterns = [
    path("", views.health_check),
    path("login", views.login),
    path("register", views.register),
    path("folders", views.folders),
    path("session/manage/logout", views.logout),
    path("session/manage/refresh", views.refresh_session),
    path("session/validate", views.validate_session),
    path("file/upload", blob_views.upload_file),
    path("file/download", blob_views.download_file),
    path("folders/contents/<uuid:folder_uuid>", views.get_files)
]
