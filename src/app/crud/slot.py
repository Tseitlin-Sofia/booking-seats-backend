from sqlalchemy import select

from app.models.slot import Slot


class CRUDSlot:
    async def get_by_cafe(self, cafe_id: int, session, status: str = 'active'):
        slots = select(Slot).where(Slot.cafe_id == cafe_id)

        if status == 'active':
            slot_crud = slots.where(Slot.is_active.is_(True))
        elif status == 'inactive':
            slot_crud = slots.where(Slot.is_active.is_(False))
        elif status == 'all':
            slot_crud = slots

        result = await session.execute(slot_crud)
        return result.scalars().all()


slot_crud = CRUDSlot()
