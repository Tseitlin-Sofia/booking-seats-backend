"""Эндпоинты для управления блюдами в кафе."""

from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.api.dependencies import ManagerDep, SessionDep, UserDep
from app.api.validators.cafe import get_cafe_or_404, is_manager_from_cafe
from app.api.validators.dish import (
    check_dish_exists_in_cafe,
    check_dish_name_unique_in_cafe,
)
from app.crud.dish import dish_crud
from app.schemas.dish import DishCreate, DishInfo, DishUpdate

router = APIRouter()


@router.get(
    '/',
    response_model=list[DishInfo],
    summary='Получение списка блюд кафе',
    description=(
        'Возвращает список блюд кафе. '
        'Администраторы и менеджеры могут фильтровать по `show_active`. '
        'Обычным пользователям возвращаются только активные и доступные блюда.'
    ),
)
async def get_dishes(
    cafe_id: int,
    session: SessionDep,
    user: UserDep,
    show_active: bool = None,
) -> list[DishInfo]:
    """Возвращает все блюда заданного кафе."""
    await get_cafe_or_404(session, cafe_id, True)
    if not (user.is_admin or user.is_manager):
        return await dish_crud.get_dishes_by_cafe(
            cafe_id=cafe_id,
            session=session,
            show_active=True,
            only_available=True,
        )
    return await dish_crud.get_dishes_by_cafe(
        cafe_id=cafe_id,
        session=session,
        show_active=show_active,
    )


@router.post(
    '/',
    response_model=DishInfo,
    status_code=HTTPStatus.CREATED,
    summary='Создание нового блюда',
    description=(
        'Создаёт блюдо в указанном кафе. '
        'Доступно администратору и менеджеру привязанного кафе.'
    ),
)
async def create_dish(
    cafe_id: int,
    dish_in: DishCreate,
    session: SessionDep,
    user: ManagerDep,
) -> DishInfo:
    """Создаёт блюдо в указанном кафе."""
    await get_cafe_or_404(session, cafe_id, True)
    if user.is_manager:
        await is_manager_from_cafe(cafe_id, user)
    await check_dish_name_unique_in_cafe(cafe_id, dish_in.name, session)
    return await dish_crud.create_for_cafe(
        cafe_id=cafe_id,
        obj_in=dish_in,
        session=session,
    )


@router.get(
    '/{dish_id}',
    response_model=DishInfo,
    summary='Получение блюда по ID',
)
async def get_dish(
    cafe_id: int,
    dish_id: int,
    session: SessionDep,
    user: UserDep,
) -> DishInfo:
    """Возвращает информацию о конкретном блюде в кафе."""
    await get_cafe_or_404(session, cafe_id, True)
    dish = await check_dish_exists_in_cafe(cafe_id, dish_id, session)
    if not (user.is_admin or user.is_manager) and (
        not dish.is_active or not dish.is_available
    ):
        raise HTTPException(HTTPStatus.FORBIDDEN, detail='Доступ запрещен!')
    return dish


@router.patch(
    '/{dish_id}',
    response_model=DishInfo,
    summary='Обновление блюда',
    description=(
        'Обновляет блюдо в указанном кафе. '
        'Доступно администратору и менеджеру привязанного кафе.'
    ),
)
async def update_dish(
    cafe_id: int,
    dish_id: int,
    dish_in: DishUpdate,
    session: SessionDep,
    user: ManagerDep,
) -> DishInfo:
    """Обновляет данные блюда в указанном кафе."""
    await get_cafe_or_404(session, cafe_id, True)
    if user.is_manager:
        await is_manager_from_cafe(cafe_id, user)
    dish = await check_dish_exists_in_cafe(cafe_id, dish_id, session)
    if dish_in.name is not None and dish_in.name != dish.name:
        await check_dish_name_unique_in_cafe(
            cafe_id=cafe_id,
            name=dish_in.name,
            session=session,
            dish_id=dish_id,
        )
    return await dish_crud.update(
        db_obj=dish,
        obj_in=dish_in,
        session=session,
    )
