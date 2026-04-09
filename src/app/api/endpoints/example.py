"""Пример модуля эндпоинтов ресурса (резервация)."""

# from typing import Annotated

# from fastapi import APIRouter, Depends
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.api.validators import (
#     check_reservation_intersections,
#     check_meeting_room_exists,
#     check_reservation_before_edit
# )
# from app.crud.reservation import reservation_crud
# from app.core.db import get_async_session
# from app.schemas.reservation import (
#     ReservationCreate, ReservationDB, ReservationUpdate
# )
# from app.core.user import current_user, current_superuser
# from app.models import User

# router = APIRouter()

# SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
# UserDep = Annotated[User, Depends(current_user)]


# @router.post('/', response_model=ReservationDB)
# async def create_reservation(
#         reservation: ReservationCreate,
#         session: SessionDep,
#         user: UserDep
# ):
#     await check_meeting_room_exists(
#         reservation.meetingroom_id, session
#     )
#     await check_reservation_intersections(
#         **reservation.model_dump(), session=session
#     )
#     new_reservation = await reservation_crud.create(
#         reservation, session, user
#     )
#     return new_reservation

# @router.get(
#     '/',
#     response_model=list[ReservationDB],
#     dependencies=[Depends(current_superuser)],
# )
# async def get_all_reservations(
#     session: SessionDep,
# ):
#     """Только для суперюзеров."""
#     all_reservations = await reservation_crud.get_multi(session)
#     return all_reservations

# @router.delete(
#     '/{reservation_id}',
#     response_model=ReservationDB,
# )
# async def delete_reservation(
#     reservation_id: int,
#     session: SessionDep,
#     user: UserDep
# ):
#     reservation = await check_reservation_before_edit(
#         reservation_id, session, user
#     )
#     reservation = await reservation_crud.remove(reservation, session)
#     return reservation

# @router.patch('/{reservation_id}', response_model=ReservationDB)
# async def update_reservation(
#     reservation_id: int,
#     obj_in: ReservationUpdate,
#     session: SessionDep,
#     user: UserDep,
# ):
#     reservation = await check_reservation_before_edit(
#         reservation_id, session, user
#     )
#     await check_reservation_intersections(
#         **obj_in.model_dump(),
#         reservation_id=reservation_id,
#         meetingroom_id=reservation.meetingroom_id,
#         session=session
#     )
#     reservation = await reservation_crud.update(
#         db_obj=reservation,
#         obj_in=obj_in,
#         session=session,
#     )
#     return reservation

# @router.get('/{meeting_room_id}/reservations',
#     response_model=list[ReservationDB],
#     response_model_exclude={'user_id'},
# )
# async def get_reservations_for_room(
#     meeting_room_id: int,
#     session: SessionDep,
# ):
#     await check_meeting_room_exists(meeting_room_id, session)
#     reservations = await reservation_crud.get_future_reservations_for_room(
#         room_id=meeting_room_id,
#         session=session,
#     )
#     return reservations

# @router.get('/my_reservations',
#     response_model=list[ReservationDB],
#     response_model_exclude={'user_id'},
# )
# async def get_reservations_for_user(
#     user: UserDep,
#     session: SessionDep,
# ):
#     """Получает список всех бронирований для текущего пользователя."""
#     reservations = await reservation_crud.get_by_user(
#         user=user,
#         session=session,
#     )
#     return reservations
