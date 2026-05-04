"""Обработчики исключений."""

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.error import ErrorResponse


async def validation_exception_handler(
    request: Request, exc: RequestValidationError,
) -> JSONResponse:
    """Обработчик ошибок валидации (422)."""
    errors = exc.errors()

    if not errors:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message='Ошибка валидации данных',
            ).model_dump(),
        )

    first_error = errors[0]
    error_type = first_error.get('type', '')
    msg = first_error.get('msg', 'Ошибка валидации данных')
    loc = first_error.get('loc', [])

    if error_type == 'json_invalid':
        message = 'Ошибка в структуре JSON запроса'
    elif error_type == 'missing' and msg == 'Field required':
        field = loc[-1] if loc else 'unknown'
        message = f'Поле «{field}» обязательно'
    else:
        if msg.startswith('Value error, '):
            msg = msg[13:]
        message = msg

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
        ).model_dump(),
    )


async def http_exception_handler(
    request: Request, exc: HTTPException,
) -> JSONResponse:
    """Обработчик HTTP-исключений."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.status_code,
            message=str(exc.detail),
        ).model_dump(),
    )


async def server_exception_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    """Обработчик непредвиденных ошибок (500)."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message='Внутренняя ошибка сервера',
        ).model_dump(),
    )
