import uuid
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient
from django.http import StreamingHttpResponse, Http404


# Configure once
BLOB_ACCOUNT_URL = "https://busblobstorage.blob.core.windows.net"
BLOB_CONTAINER_NAME = "data"

credential = ManagedIdentityCredential()  # Or User Assigned MI
blob_service_client = BlobServiceClient(account_url=BLOB_ACCOUNT_URL, credential=credential)


@csrf_exempt
@require_POST
def upload_file(request):
    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    if file.size > getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024):
        return JsonResponse({"error": "File too large"}, status=400)

    # Generate unique blob name
    blob_name = f"{uuid.uuid4()}_{file.name}"

    # Upload to Azure Blob Storage streaming
    blob_client = blob_service_client.get_blob_client(container=BLOB_CONTAINER_NAME, blob=blob_name)
    blob_client.upload_blob(file.file, overwrite=True, content_type=file.content_type)

    return JsonResponse({
        "id": blob_name,
        "original_name": file.name,
        "size": file.size
    })


@csrf_exempt
@require_POST
def download_file(request):
    data = json.loads(request.body)
    filename = data["filename"]
    blob_client = blob_service_client.get_blob_client(container=BLOB_CONTAINER_NAME, blob=filename)

    if not blob_client.exists():
        raise Http404("File not found")

    stream = blob_client.download_blob()

    response = StreamingHttpResponse(
        stream.chunks(),  # stream chunks from Azure
        content_type="application/octet-stream"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response

