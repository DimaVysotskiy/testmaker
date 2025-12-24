from fastapi import APIRouter, Depends, UploadFile, File


from ..utils import get_minio, MinioManager, require_roles
from ..enums import UserRole
import uuid




task_router = APIRouter(prefix="/tasks", tags=["tasks"])




@task_router.post("/upload", dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))])
async def upload_file(
    file: UploadFile = File(...),
    minio: MinioManager = Depends(get_minio)
):
    file_id = str(uuid.uuid4())
    extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    object_name = f"{file_id}.{extension}" if extension else file_id
    
    file_url = await minio.upload_file(file, object_name)
    
    return {"file_url": file_url, "object_name": object_name}