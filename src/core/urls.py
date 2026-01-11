from django.urls import path
from . import views

urlpatterns = [
    path("", views.health_check),
    path("login", views.login),
    path("register", views.register),
    path("session/manage/logout", views.logout),
    path("session/manage/refresh", views.refresh_session),
    path("session/validate", views.validate_session)
]
