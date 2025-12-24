from ..repo import BaseRepository
from ..models import UserInDB
from sqlalchemy.future import select
from ..utils import sessionmaker, get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession




class UserRepository(BaseRepository[UserInDB]):
    def __init__(self, model, session: AsyncSession = Depends(get_db)):
        super().__init__(model, session)
    
    async def get_by_username(self, username: str) -> UserInDB | None:
        statement = select(self.model).where(self.model.username == username)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()



user_repo = UserRepository(UserInDB)