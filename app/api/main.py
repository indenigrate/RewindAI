from fastapi import FastAPI
from app.api.commands import router as command_router

app = FastAPI(title="RewindAI Command API")

app.include_router(command_router)
