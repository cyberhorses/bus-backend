import json
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from core.services.auth_service import verify_user_credentials, create_user
from core.services.jwt import (
    create_access_token,
    validate_jwt,
    decode_user_uuid,
    create_refresh_token,
    validate_refresh_jwt,
    expire_refresh_token,
    get_user_from_refresh_token,
)
from core.services.helpers import increment_token_version, get_user_by_uuid
from django.views.decorators.csrf import csrf_exempt
import uuid


def health_check(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def validate_session(request: HttpRequest) -> JsonResponse:
    """
    GET /session/validate
    Cookie: access_token=...
    """
    token = request.COOKIES.get("access_token")
    if token is not None and validate_jwt(token):
        return JsonResponse({"message": "success"})

    return JsonResponse({"error": "Session expired" if token else "Invalid session"}, status=401)


def logout(request: HttpRequest) -> JsonResponse:
    """
    GET /session/manage/logout
    Cookie: access_token=...;refresh_token=...
    """
    acc_token = request.COOKIES.get("access_token")
    ref_token = request.COOKIES.get("refresh_token")

    if ref_token is not None and validate_refresh_jwt(ref_token):
        expire_refresh_token(ref_token)
    if acc_token is not None and validate_jwt(acc_token):
        increment_token_version(decode_user_uuid(acc_token))
        return JsonResponse({"message": "success"})

    return JsonResponse({"error": "Invalid session"}, status=403)


@csrf_exempt  # TODO
@require_POST
def login(request: HttpRequest):
    """
    POST /login
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

    jwt = create_access_token(username)
    refresh_token = create_refresh_token(username)
    response = JsonResponse({"message": "success"})

    # TODO secure=True
    response.set_cookie("access_token", jwt, httponly=True, samesite="Lax")
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="Lax", path="/api/session/manage/")

    return response


@csrf_exempt  # TODO
@require_POST
def register(request: HttpRequest):
    """
    POST /register
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

    return JsonResponse({"message": "success"})


def refresh_session(request: HttpRequest):
    """
    GET /session/manage/refresh
    Cookie: refresh_token=...
    """
    ref_token = request.COOKIES.get("refresh_token")
    if ref_token is not None and validate_refresh_jwt(ref_token):
        expire_refresh_token(ref_token)

        user_uuid = get_user_from_refresh_token(ref_token)
        username = str(get_user_by_uuid(user_uuid).username)
        acc_token = create_access_token(username)
        ref_token = create_refresh_token(username)

        response = JsonResponse({"message": "success"})
        response.set_cookie("access_token", acc_token, httponly=True, samesite="Lax")
        response.set_cookie("refresh_token", ref_token, httponly=True, samesite="Lax", path="/api/session/manage/")
        return response
    return JsonResponse({"message": "Invalid refresh token"}, status=401)
