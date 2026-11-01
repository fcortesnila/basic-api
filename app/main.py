from fastapi import FastAPI

from app.routes import router

app = FastAPI(
    title="Basic Phone Directory API",
    description="A small in-memory phone directory with create, edit, and delete operations.",
    version="1.0.0",
)
app.include_router(router)
