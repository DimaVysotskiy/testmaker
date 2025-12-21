from fastapi import FastAPI
from routers import ai_tools_router

app = FastAPI()

app.include_router(ai_tools_router)

@app.get("/ping")
def ping():
    return {"message": "pong"}