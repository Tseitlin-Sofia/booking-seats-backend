from fastapi import HTTPException, File, UploadFile

from app.core.constants import MediaConstants


async def validate_image(file: UploadFile = File(...)) -> bytes:
    """Валидирует и возвращает содержимое файла"""
    if file.content_type not in MediaConstants.VALID_TYPES:
        raise HTTPException(400, "Выберете изображение в формате png или jpeg")

    content = await file.read()

    if len(content) > MediaConstants.MAX_PHOTO_SIZE:
        raise HTTPException(400, "Размер файла не должен превышать 5MB")

    return content
