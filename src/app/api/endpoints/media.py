"""Модуль эндпоинтов для загрузки на сервер и получения из него изображений."""
import uuid
from datetime import datetime, timedelta

import aiofiles
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.dependencies import UserDep
from app.api.validators.media_validators import validate_image
from app.core.constants import MediaConstants
from app.celery.tasks import notify_client, notify_admin
from app.models.user import User
from app.services.media_service import transform_to_jpeg

router = APIRouter()

def is_manager_or_admin(user: User) -> None:
    """Проверка авторзованного юзера на роль админа/менеджера."""
    if user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для этого действия.",
        )

@router.post(
    '/',
    summary="Загрузить png/jpeg на сервер",
    status_code=201
)
async def load_photo_to_server(
    current_user: UserDep,
    image_bytes: bytes = Depends(validate_image),
) -> dict:
    """Загрузка png/jpg изображений на сервер в папку src/media/.

    Ограничение: объем не более 5MB, только для админа/менеджера.
    """
    is_manager_or_admin(current_user)
    MediaConstants.MEDIA_DIR.mkdir(exist_ok=True)

    while True:
        media_id = uuid.uuid4()
        filename = f"{media_id}.{MediaConstants.IMAGE_EXTENSION}"
        file_path = MediaConstants.MEDIA_DIR / filename

        if not file_path.exists():
            break

    jpeg_bytes = transform_to_jpeg(image_bytes)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(jpeg_bytes)
    notify_admin.delay()
    notify_client.apply_async(
        args=[],
        eta=datetime.now() + timedelta(minutes=1)
    )

    return {"media_id": media_id}


@router.get('/{media_id}', summary="Получить фото по его ID")
async def get_photo(media_id: str) -> FileResponse:
    """Возврат клиенту фотографии."""
    filename = f"{media_id}.{MediaConstants.IMAGE_EXTENSION}"
    file_path = MediaConstants.MEDIA_DIR / filename
    if not file_path.exists():
        detail = "Фото не найдено! Убедитесь, что правильно указали id."
        raise HTTPException(status_code=404, detail=detail)
    return FileResponse(
        path=file_path,
        media_type="image/jpeg",
        filename=filename,
    )
