from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from database import db, client, FRONTEND_BUILD_DIR
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI()

# Import and include all routers
from routers.auth import router as auth_router
from routers.family import router as family_router
from routers.calendar import router as calendar_router
from routers.shopping import router as shopping_router
from routers.tasks import router as tasks_router
from routers.chores import router as chores_router
from routers.notes import router as notes_router
from routers.budget import router as budget_router
from routers.meals import router as meals_router
from routers.recipes import router as recipes_router
from routers.grocery import router as grocery_router
from routers.contacts import router as contacts_router
from routers.pantry import router as pantry_router
from routers.settings import router as settings_router
from routers.suggestions import router as suggestions_router
from routers.utilities import router as utilities_router
from routers.websocket import router as websocket_router

app.include_router(auth_router)
app.include_router(family_router)
app.include_router(calendar_router)
app.include_router(shopping_router)
app.include_router(tasks_router)
app.include_router(chores_router)
app.include_router(notes_router)
app.include_router(budget_router)
app.include_router(meals_router)
app.include_router(recipes_router)
app.include_router(grocery_router)
app.include_router(contacts_router)
app.include_router(pantry_router)
app.include_router(settings_router)
app.include_router(suggestions_router)
app.include_router(utilities_router)
app.include_router(websocket_router)


# Health & root
@app.get("/api/")
async def root():
    return {"message": "Family Hub API", "status": "running", "version": "2.1.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend build (Docker production mode)
if FRONTEND_BUILD_DIR.exists():
    static_dir = FRONTEND_BUILD_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_root():
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        file_path = FRONTEND_BUILD_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
