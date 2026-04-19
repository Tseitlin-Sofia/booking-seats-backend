from typing import Any

# from fastapi import HTTPException


async def check_slots_intersections(**kwargs: Any) -> None:
    """Проверяет пересечение временных слотов."""
    # reservations = await reservation_crud.get_reservations_at_the_same_time(
    #     **kwargs,
    # )
    # if reservations:
    #     raise HTTPException(
    #         status_code=422,
    #         detail=str(reservations),
    #     )
