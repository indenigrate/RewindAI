from fastapi import FastAPI

from app.api.commands import router as command_router
from app.api.reads import router as read_router

app = FastAPI(title="RewindAI API")

# Command APIs (write side)
app.include_router(command_router)

# Read APIs (projection-backed)
app.include_router(read_router)
