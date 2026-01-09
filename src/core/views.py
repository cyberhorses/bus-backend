import json
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from core.services.auth_service import verify_user_credentials, create_user
from django.views.decorators.csrf import csrf_exempt
import uuid

def health_check(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})

@csrf_exempt
@require_POST
def login(request: HttpRequest):
    """
    Body: JSON { "username": "...", "password": "..." }
    """
    try:
        data = json.loads(request.body)
        username = data["username"]
        password = data["password"]
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid request"}, status=400)

    user = verify_user_credentials(username, password)
    if not user:
        return JsonResponse({"error": "Invalid username or password"}, status=401)

    return JsonResponse({"ok": True, "user_id": str(user.id)})

@csrf_exempt
@require_POST
def register(request: HttpRequest):
    """
    POST /auth/register
    Body: { "username": "...", "password": "..." }
    """
    try:
        data = json.loads(request.body)
        username = data["username"]
        password = data["password"]
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid request"}, status=400)

    if not username or not password:
        return JsonResponse({"error": "Username and password required"}, status=400)

    user = create_user(username=username, password=password)
    if not user:
        return JsonResponse({"error": "Username already exists"}, status=409)

    return JsonResponse({"ok": True, "user_id": str(user.id)})
