from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import ai_tools_router, o2auth_router, user_router
from .utils import sessionmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    sessionmanager.init_db()
    yield
    await sessionmanager.close()

app = FastAPI(lifespan=lifespan)

app.include_router(ai_tools_router)
app.include_router(o2auth_router)
app.include_router(user_router)


@app.get("/ping")
def ping():
    return {"message": "pong"}