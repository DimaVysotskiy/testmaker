from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import ai_tools_router, o2auth_router, user_router, task_router, answer_router
from .utils import sessionmanager, minio_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    sessionmanager.init_db()
    await minio_manager.init_minio()
    yield
    await sessionmanager.close()
    await minio_manager.close()


app = FastAPI(
    lifespan=lifespan,
    swagger_ui_parameters={"operationsSorter": 'method'}
    )

app.include_router(ai_tools_router)
app.include_router(o2auth_router)
app.include_router(user_router)
app.include_router(task_router)
app.include_router(answer_router)


@app.get("/ping")
def ping():
    return {"message": "pong"}