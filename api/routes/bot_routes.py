"""
Bot control routes for the Delta bot API.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Logger
logger = logging.getLogger("BotRoutes")

# Router
router = APIRouter()

# Bot instance (set at runtime)
bot = None

class BotResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@router.post("/start")
async def start_bot():
    """Start the bot's trading operations."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        # Start the bot's execution
        if hasattr(bot, 'start') and not bot._is_running:
            # Starting outside of main to avoid blocking
            await bot.execute_best_delta_strategy()
            
            return BotResponse(
                success=True,
                message="Bot started successfully"
            )
        else:
            return BotResponse(
                success=False,
                message="Bot is already running"
            )
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_bot():
    """Stop the bot's trading operations."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        # Stop the bot but keep the API running
        await bot.close_all_delta_positions()
        
        return BotResponse(
            success=True,
            message="Bot stopped successfully"
        )
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/close-position/{coin}")
async def close_position(coin: str):
    """Close a specific position."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        # Check if the coin is valid
        if coin not in bot.tracked_coins:
            raise HTTPException(status_code=400, detail=f"Invalid coin: {coin}")
        
        # Close the position
        result = await bot.close_delta_position(coin)
        
        return BotResponse(
            success=True,
            message=f"Closed position for {coin}",
            data={"result": result}
        )
    except Exception as e:
        logger.error(f"Error closing position for {coin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-position/{coin}")
async def create_position(coin: str):
    """Create a position for a specific coin."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        # Check if the coin is valid
        if coin not in bot.tracked_coins:
            raise HTTPException(status_code=400, detail=f"Invalid coin: {coin}")
        
        # Create the position
        result = await bot.create_delta_position(coin)
        
        return BotResponse(
            success=True,
            message=f"Created position for {coin}",
            data={"result": result}
        )
    except Exception as e:
        logger.error(f"Error creating position for {coin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/state")
async def get_bot_state():
    """Get the current state of the bot."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        # Return basic bot state
        return BotResponse(
            success=True,
            message="Got bot state",
            data={"running": hasattr(bot, '_is_running') and bot._is_running}
        )
    except Exception as e:
        logger.error(f"Error getting bot state: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 