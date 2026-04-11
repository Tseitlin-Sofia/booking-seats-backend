from fastapi import HTTPException, File, UploadFile


MAX_PHOTO_SIZE = 1024 * 1024 * 5
VALID_TYPES = ["image/png", "image/jpeg"]

async def validate_image(file: UploadFile = File(...)) -> bytes:
    """Валидирует и возвращает содержимое файла"""
    if file.content_type not in VALID_TYPES:
        raise HTTPException(400, "Выберете изображение в формате png или jpeg")

    content = await file.read()

    if len(content) > MAX_PHOTO_SIZE:
        raise HTTPException(400, "Размер файла не должен превышать 5MB")

    return content
