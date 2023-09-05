from fastapi import APIRouter, UploadFile, Depends

from auth import get_current_user
from config import Configuration, s3
from models import User

router = APIRouter()


@router.post("/upload/{category}")
async def upload_photo(file: UploadFile, category: str, user: User = Depends(get_current_user)):
    filename = str(user.id) + "/" + category + "/" + file.filename.lower()
    s3.upload_fileobj(file.file, Configuration.aws_bucket_name, filename)
    return {'filename': filename, 'user_id': user.id}
