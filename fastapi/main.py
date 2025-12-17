from contextlib import asynccontextmanager
from fastapi import FastAPI
import sys
from pathlib import Path

# Add current directory to path for imports
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from core import sessionmanager
from app.routers import user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    sessionmanager.init_main_db()
    yield
    await sessionmanager.close()

app = FastAPI(
    title="Moodle API",
    description="API для системы управления обучением",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(user_router.router)