from fastapi import APIRouter, HTTPException, status
from app.api.dependencies import SessionDep
from app.schemas.auth import AuthData, AuthToken
from app.core.user import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=AuthToken,
    summary="Получение токена авторизации",
    description="Возвращает токен для последующей авторизации пользователя.",
    response_description="Токен доступа",
)
async def login(
    auth_data: AuthData,
    session: SessionDep,
) -> AuthToken:
    """
    Аутентификация пользователя по email/phone и паролю.
    Возвращает JWT-токен при успешной аутентификации.
    """
    auth_service = AuthService(session)
    user = await auth_service.authenticate_user(
        email=auth_data.email,
        phone=auth_data.phone,
        password=auth_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Неверные имя пользователя или пароль",
        )
    token = AuthService.create_token(user.id, user.role)
    return AuthToken(access_token=token, token_type="bearer")
