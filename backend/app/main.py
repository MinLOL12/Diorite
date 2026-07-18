from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import os
from pathlib import Path

from .core.websocket_manager import manager
from .api.routes import projects, files, builds, processes, cache, templates, ai, scaffolds, settings

app = FastAPI(
    title="Diorite API",
    description="Zero-setup Minecraft modding IDE backend - manages projects, files, builds, Minecraft processes, caching, templates, AI context, and settings",
    version="0.1.0"
)

# CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router)
app.include_router(files.router)
app.include_router(builds.router)
app.include_router(processes.router)
app.include_router(cache.router)
app.include_router(templates.router)
app.include_router(ai.router)
app.include_router(scaffolds.router)
app.include_router(settings.router)

@app.get("/")
def root():
    return {
        "name": "Diorite Backend",
        "version": "0.1.0",
        "description": "Minecraft zero-setup IDE backend",
        "docs": "/docs",
        "status": "running",
        "features": [
            "Projects from templates (Fabric, NeoForge, Forge, Quilt)",
            "Cache reuse for Java, Gradle, Minecraft, mappings, loaders",
            "File editing via API",
            "One-click Play: build + launch Minecraft",
            "Live log streaming via WebSockets",
            "Process management (stop/restart/crash detection)",
            "Project-aware AI context",
            "Scaffold actions: block, item, entity, screen, recipe, data component",
            "Modular services"
        ]
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "diorite-backend"}

# WebSocket endpoints
@app.websocket("/ws/{channel}/{project_id}")
async def websocket_channel(websocket: WebSocket, channel: str, project_id: str):
    """
    Generic WS per channel per project.
    channel can be: build, logs, process, files
    """
    full_channel = f"{channel}:{project_id}"
    await manager.connect(websocket, full_channel)
    # Also connect to global for monitoring
    try:
        while True:
            # Keep alive and receive client messages (e.g., ping, file save notifications)
            try:
                data = await websocket.receive_text()
                # Echo or handle
                # If client sends JSON with type, we can process
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except:
                    pass
            except WebSocketDisconnect:
                break
            except Exception:
                break
    finally:
        await manager.disconnect(websocket, full_channel)

@app.websocket("/ws/global")
async def websocket_global(websocket: WebSocket):
    channel = "global"
    await manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, channel)

if __name__ == "__main__":
    import multiprocessing
    import sys

    import uvicorn

    multiprocessing.freeze_support()
    port = int(os.getenv("DIORITE_PORT", "7331"))
    frozen = getattr(sys, "frozen", False)
    # reload spawns child processes — only sensible in source checkouts
    if frozen:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    else:
        uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)
