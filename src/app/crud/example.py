"""Пример CRUD операции для модели."""

# from datetime import datetime

# from sqlalchemy import and_, between, func, or_, select
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.crud.base import CRUDBase
# from app.models import Reservation, User

# class CRUDReservation(CRUDBase):
#     async def get_future_reservations_for_room(
#         self,
#         room_id: int,
#         session: AsyncSession,
#     ) -> list[Reservation]:
#         reservations = await session.execute(select(Reservation).where(
#             Reservation.meetingroom_id == room_id,
#             Reservation.from_reserve > datetime.now()
#         ))
#         return list(reservations.scalars().all())

#     async def get_reservations_at_the_same_time(
#             self,
#             *,
#             from_reserve: datetime,
#             to_reserve: datetime,
#             meetingroom_id: int,
#             reservation_id: int | None = None,
#             session: AsyncSession,
#         ) -> list[Reservation]:
#             statement = select(Reservation).where(
#                 Reservation.meetingroom_id == meetingroom_id,
#                 from_reserve <= Reservation.to_reserve,
#                 to_reserve >= Reservation.from_reserve
#             )
#             if reservation_id is not None:
#                 statement = statement.where(
#                     Reservation.id != reservation_id
#                 )
#             reservations = await session.execute(statement)
#             reservations = list(reservations.scalars().all())
#             return reservations

#     async def get_by_user(
#         self,
#         user: User,
#         session: AsyncSession,
#     ) -> list[Reservation]:
#         reservations = await session.execute(
#             select(Reservation).where(Reservation.user_id == user.id)
#         )
#         return list(reservations.scalars().all())

#     async def get_count_res_at_the_same_time(
#             self,
#             from_reserve: datetime,
#             to_reserve: datetime,
#             session: AsyncSession,
#     ) -> list[dict[str, int]]:
#         reservations = await session.execute(
#             select(Reservation.meetingroom_id,
#                     func.count(Reservation.meetingroom_id)).where(
#                 Reservation.from_reserve >= from_reserve,
#                 Reservation.to_reserve <= to_reserve
#             ).group_by(Reservation.meetingroom_id)
#         )
#         reservations = reservations.all()
#         res = [
#             {"meetingroom_id": room_id, "count": count}
#             for room_id, count in reservations
#         ]
#         return res


# reservation_crud = CRUDReservation(Reservation)
