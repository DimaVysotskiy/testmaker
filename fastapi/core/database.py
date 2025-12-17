from __future__ import annotations

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, StaticPool
from sqlalchemy.sql import text

from .config import settings

class SessionManager:
    """Manages asynchronous DB sessions with connection pooling."""

    def __init__(self) -> None:
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def init_main_db(self) -> None:
        """Инициализация основной БД"""
        self.engine = create_async_engine(
            settings.MAIN_BD_URL,
            poolclass=AsyncAdaptedQueuePool,
            pool_pre_ping=True,
        )
        self._create_factory()

    def init_test_db(self) -> None:
        """Инициализация БД для pytest"""
        url = settings.TEST_BD_URL
        
        self.engine = create_async_engine(
            url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        self._create_factory()

    def _create_factory(self) -> None:
        """Internal helper to create session factory once engine is set."""
        if self.engine:
            self.session_factory = async_sessionmaker(
                self.engine,
                expire_on_commit=False,
                autoflush=False,
                class_=AsyncSession,
            )

    async def close(self) -> None:
        """Dispose of the database engine."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a database session."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not initialized. Call init_main_db or init_test_db first.")

        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e


sessionmanager = SessionManager()