import json
from django.conf import settings
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient
from django.http import StreamingHttpResponse, Http404
from core.services.jwt import validate_jwt, decode_user_uuid
from core.services.helpers import get_folder_by_uuid, get_user_folder_permissions, get_user_by_uuid, get_file_by_uuid
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from core.models import File


credential = ManagedIdentityCredential()  # Or User Assigned MI
blob_service_client = BlobServiceClient(account_url=settings.BLOB_ACCOUNT_URL, credential=credential)


@csrf_exempt
@require_POST
def upload_file(request):
    """
    POST /file/upload
    Cookie: acces_token=...
    Content-type: multipart/form-data

    -------
    file
    -------
    dir
    -------
    """
    # 1. Check user's JWT token
    token = request.COOKIES.get("access_token")
    if not token or not validate_jwt(token):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # 2. Get file data
    file = request.FILES.get("file")
    dir = request.POST.get("dir")
    if not file or not dir:
        return JsonResponse({"error": "No file uploaded"}, status=400)
    if file.size > getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024):
        return JsonResponse({"error": "File too large"}, status=400)

    # 3. Check if user has dir access
    folder = get_folder_by_uuid(dir)
    user = get_user_by_uuid(decode_user_uuid(token))
    if not folder or not user:
        return JsonResponse({"error": "Forbidden"}, status=403)

    if "upload" not in get_user_folder_permissions(folder, user):
        return JsonResponse({"error": "Forbidden"}, status=403)
    

    file_db = File.objects.create(
            name=file.name,
            folder=folder,
            size = file.size
        )
    blob_name = f"{file_db.id}_{file_db.name}"

    blob_client = blob_service_client.get_blob_client(container=settings.BLOB_CONTAINER_NAME, blob=blob_name)
    blob_client.upload_blob(file.file, overwrite=True, content_type=file.content_type)

    return JsonResponse({
        "id": blob_name,
        "original_name": file.name,
        "size": file.size
    })

@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def get_delete_file(request: HttpRequest, file_id: str):
    # 1. Check user's JWT token
    token = request.COOKIES.get("access_token")
    if not token or not validate_jwt(token):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # 2. Get file details
    data = json.loads(request.body)
    file_id = data["file_id"]

    # 3. Get file and user
    file = get_file_by_uuid(file_id)
    user = get_user_by_uuid(decode_user_uuid(token))
    if not file or not user:
        return JsonResponse({"error": "Forbidden"}, status=403)

    perm, func = ("read", download_file) if request.method == "GET" else ("delete", delete_file)

    # 4. Check user's permissions
    if perm not in get_user_folder_permissions(file.folder, user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    filename = f"{file.id}_{file.name}"
    blob_client = blob_service_client.get_blob_client(container=settings.BLOB_CONTAINER_NAME, blob=filename)

    if not blob_client.exists():
        return JsonResponse({"error": "file not found"}, status=500)

    # 5. Perform the operation
    return func(blob_client=blob_client, filename=filename, file=file)


def download_file(**kwargs):

    stream = kwargs["blob_client"].download_blob()

    response = StreamingHttpResponse(
        stream.chunks(),  # stream chunks from Azure
        content_type="application/octet-stream"
    )
    response["Content-Disposition"] = f'attachment; filename="{kwargs["filename"]}"'

    return response


def delete_file(**kwargs):
    kwargs["blob_client"].delete_blob()
    kwargs["file"].delete()
    return JsonResponse({"message": "success"})



