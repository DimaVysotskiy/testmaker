from typing import Type, TypeVar, Generic, List, Dict, Any, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlmodel import SQLModel
from fastapi import HTTPException
import uuid

T = TypeVar("T", bound=SQLModel)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, data: Dict[str, Any], commit: bool = True) -> T:
        try:
            obj = self.model(**data)
            self.session.add(obj)
            if commit:
                await self.session.commit()
                await self.session.refresh(obj)
            return obj
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    async def get(self, id: uuid.UUID) -> T | None:
        # В асинхронной версии используем await session.get()
        return await self.session.get(self.model, id)

    async def get_all(self) -> Sequence[T]:
        # session.exec в SQLModel синхронный, для асинхронности используем session.execute
        statement = select(self.model)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def update(self, id: uuid.UUID, data: Dict[str, Any], commit: bool = True) -> T:
        obj = await self.get(id)
        if not obj:
            raise HTTPException(status_code=404, detail="Item not found")

        for key, value in data.items():
            setattr(obj, key, value)

        if commit:
            await self.session.commit()
            await self.session.refresh(obj)

        return obj

    async def delete(self, id: uuid.UUID, commit: bool = True) -> bool:
        obj = await self.get(id)
        if not obj:
            raise HTTPException(status_code=404, detail="Item not found")

        await self.session.delete(obj)
        if commit:
            await self.session.commit()
        return True