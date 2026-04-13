import io

from PIL import Image


def transform_to_jpeg(image_bytes: bytes) -> bytes:
    """Преобразует png в jpeg"""
    image = Image.open(io.BytesIO(image_bytes))
    # Конвертируем в RGB (JPEG не поддерживает прозрачность)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=85)
    return output.getvalue()
