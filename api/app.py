"""
API server for Delta bot.
"""

import os
import asyncio
import logging
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .utils.auth import verify_api_key
from .routes import bot_routes, status_routes, config_routes
from .websocket_manager import manager

# Global instances
app = FastAPI(title="Delta Bot API", description="API for controlling the Delta bot")
server = None

# Add a WebSocket endpoint for logs
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)


bot_instance = None

# Configure logging
logger = logging.getLogger("DeltaAPI")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    bot_routes.router,
    prefix="/api/bot",
    tags=["bot"],
    dependencies=[Depends(verify_api_key)]
)

app.include_router(
    status_routes.router,
    prefix="/api/status",
    tags=["status"],
    dependencies=[Depends(verify_api_key)]
)

app.include_router(
    config_routes.router,
    prefix="/api/config",
    tags=["config"],
    dependencies=[Depends(verify_api_key)]
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

async def start_api(bot, host="0.0.0.0", port=8080):
    """Start the API server."""
    global bot_instance, server
    
    bot_instance = bot
    
    # Set the bot instance for the routers
    bot_routes.bot = bot
    status_routes.bot = bot
    config_routes.bot = bot
    
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    
    # Start the server in a separate task
    asyncio.create_task(server.serve())
    
    return server

async def stop_api():
    """Stop the API server."""
    global server
    
    if server:
        logger.info("Stopping API server...")
        await server.shutdown()
        logger.info("API server stopped")

# Export the app instance for use in other modules
__all__ = ["app", "start_api", "stop_api"] 