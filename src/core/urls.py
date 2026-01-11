from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health_check),
    path("login", views.login),
    path("register", views.register),
    path("logout", views.logout),
    path("session/validate", views.validate_session)
]
