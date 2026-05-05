"""Валидаторы для эндпоинтов блюд."""

from http import HTTPStatus
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validators.cafe import raise_error
from app.core.constants import DishConstants
from app.core.logging import get_logger
from app.crud.dish import dish_crud
from app.models.dish import Dish

logger = get_logger()


async def check_dish_exists_in_cafe(
    cafe_id: int,
    dish_id: int,
    session: AsyncSession,
) -> Dish:
    """Проверяет, что блюдо существует в данном кафе."""
    dish = await dish_crud.get_dish_in_cafe(cafe_id, dish_id, session)
    if dish is None:
        msg = DishConstants.DISH_NOT_FOUND_IN_CAFE.format(
            dish_id=dish_id,
            cafe_id=cafe_id,
        )
        logger.debug(msg)
        await raise_error(msg, HTTPStatus.NOT_FOUND)
    return dish


async def check_dish_name_unique_in_cafe(
    cafe_id: int,
    name: str,
    session: AsyncSession,
    dish_id: Optional[int] = None,
) -> None:
    """Проверяет уникальность названия блюда в пределах кафе.

    При PATCH передаётся `dish_id` редактируемого блюда — оно исключается
    из проверки, чтобы PATCH без смены имени или с тем же именем не падал.
    """
    existing = await dish_crud.get_by_name_in_cafe(cafe_id, name, session)
    if existing is None:
        return
    if dish_id is not None and existing.id == dish_id:
        return
    msg = DishConstants.DISH_NAME_DUPLICATE.format(
        name=name,
        cafe_id=cafe_id,
    )
    logger.debug(msg)
    await raise_error(msg, HTTPStatus.UNPROCESSABLE_ENTITY)
