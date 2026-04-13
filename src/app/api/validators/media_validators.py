from fastapi import HTTPException, File, UploadFile

from app.core.constants import MediaConstants


async def validate_image(file: UploadFile = File(...)) -> bytes:
    """Валидирует и возвращает содержимое файла"""

    if (
        not file.content_type or
        file.content_type not in MediaConstants.VALID_TYPES
    ):
        raise HTTPException(400, "Выберете изображение в формате png или jpeg")

    total = 0
    chunks = []
    while True:
        chunk = await file.read(MediaConstants.CHUNK_SIZE_1MB)
        if not chunk:
            break
        total += len(chunk)
        if total > MediaConstants.MAX_PHOTO_SIZE_5MB:
            raise HTTPException(400, "Размер файла не должен превышать 5MB")
        chunks.append(chunk)

    return b"".join(chunks)
