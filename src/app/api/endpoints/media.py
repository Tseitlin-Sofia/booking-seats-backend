"""Модуль эндпоинтов для загрузки на сервер и получения из него изображений."""
from pathlib import Path
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
# from PIL import Image


from app.core.db import get_async_session
from app.api.validators.media_validators import validate_image

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media"
IMAGE_EXTENSION = "jpg"

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
# UserDep = Annotated[User, Depends(current_user)]


@router.post('/')
async def load_photo_to_server(image_bytes: bytes = Depends(validate_image)):
    """Загрузка png/jpg изображений на сервер в папку src/media"""
    media_id = uuid.uuid4()
    filename = f"{media_id}.{IMAGE_EXTENSION}"
    file_path = MEDIA_DIR / filename
    MEDIA_DIR.mkdir(exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(image_bytes)
    return {"media_id": media_id}

    
    

    
    
