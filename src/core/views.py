import json
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST, require_GET, require_http_methods
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
from core.services.folders_operations import create_folder_for_user, get_available_folders
from core.services.helpers import increment_token_version, get_user_by_uuid
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@require_GET
def validate_session(request: HttpRequest) -> JsonResponse:
    """
    GET /session/validate
    Cookie: access_token=...
    """
    token = request.COOKIES.get("access_token")
    if token is not None and validate_jwt(token):
        return JsonResponse({"message": "success"})

    return JsonResponse({"error": "Session expired" if token else "Invalid session"}, status=401)


@require_GET
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
    response.set_cookie("access_token", jwt, httponly=True, samesite="Lax", secure=True)
    response.set_cookie(
        "refresh_token", refresh_token, httponly=True, samesite="Lax", path="/api/session/manage/", secure=True
    )

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


@require_GET
def refresh_session(request: HttpRequest) -> JsonResponse:
    """
    GET /session/manage/refresh
    Cookie: refresh_token=...
    """
    ref_token = request.COOKIES.get("refresh_token")
    if ref_token is not None and validate_refresh_jwt(ref_token):
        expire_refresh_token(ref_token)

        user = get_user_from_refresh_token(ref_token)
        if not user:
            raise ValueError("User not found")
        acc_token = create_access_token(user.username)
        ref_token = create_refresh_token(user.username)

        response = JsonResponse({"message": "success"})
        response.set_cookie("access_token", acc_token, httponly=True, samesite="Lax", secure=True)
        response.set_cookie(
            "refresh_token", ref_token, httponly=True, samesite="Lax", path="/api/session/manage/", secure=True
        )
        return response
    elif ref_token is None:
        return JsonResponse({"message": "Unauthorized"}, status=401)
    else:
        return JsonResponse({"message": "Forbidden"}, status=403)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def folders(request: HttpRequest) -> JsonResponse:
    """
    POST /register
    Cookie: access_token=...
    Body: { "name": "" }
    """
    token = request.COOKIES.get("access_token")

    if token is None:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    elif not validate_jwt(token):
        return JsonResponse({"error": "Forbidden"}, status=403)

    user_id = decode_user_uuid(token)

    if request.method == "GET":
        return _handle_get_folders(user_id, request)
    else:
        return _handle_post_folders(user_id, request)


def _handle_get_folders(user_id: str, request: HttpRequest):
    page_size = int(request.GET.get("pageSize", 5))
    page = int(request.GET.get("page", 1))
    folders = get_available_folders(user_id)

    paginator = Paginator(folders, page_size)

    try:
        page = paginator.page(page)
    except EmptyPage:
        return JsonResponse({"error": "Invalid pagination data"}, status=400)

    return JsonResponse({"items": page.object_list, "page": page.number, "totalPages": paginator.num_pages})


def _handle_post_folders(user_id: str, request: HttpRequest):
    try:
        folder_name = json.loads(request.body)["name"]

        folder = create_folder_for_user(name=folder_name, owner_id=user_id)
    except ValidationError as e:
        return JsonResponse({"error": e.message}, status=400)
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid request"}, status=400)

    return JsonResponse({"message": "Folder successfully created", "folder_id": folder.id}, status=201)
