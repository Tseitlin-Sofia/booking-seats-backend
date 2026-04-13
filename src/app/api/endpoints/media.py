"""Модуль эндпоинтов для загрузки на сервер и получения из него изображений."""
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.core.db import get_async_session
from app.api.validators.media_validators import validate_image
from app.services.media_service import transform_to_jpeg
from app.core.constants import MediaConstants

router = APIRouter()

# SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
# UserDep = Annotated[User, Depends(current_user)]


@router.post('/')
async def load_photo_to_server(image_bytes: bytes = Depends(validate_image)):
    """Загрузка png/jpg изображений на сервер в папку src/media/"""
    media_id = uuid.uuid4()
    filename = f"{media_id}.{MediaConstants.IMAGE_EXTENSION}"
    jpeg_bytes = transform_to_jpeg(image_bytes)

    file_path = MediaConstants.MEDIA_DIR / filename
    MediaConstants.MEDIA_DIR.mkdir(exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(jpeg_bytes)
    return {"media_id": media_id}


@router.get('/{media_id}')
async def get_photo(media_id: str):
    """Возврат клиенту фотографии"""
    filename = f"{media_id}.{MediaConstants.IMAGE_EXTENSION}"
    file_path = MediaConstants.MEDIA_DIR / filename
    if not file_path.exists():
        detail = "Фото не найдено! Убедитесь, что правильно указали id."
        raise HTTPException(status_code=404, detail=detail)
    return FileResponse(
        path=file_path,
        media_type="image/jpeg",
        filename=filename
    )
