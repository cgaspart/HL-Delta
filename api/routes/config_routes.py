"""
Configuration routes for the Delta bot API.
"""

import json
import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Logger
logger = logging.getLogger("ConfigRoutes")

# Router
router = APIRouter()

# Bot instance (set at runtime)
bot = None

class ConfigResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@router.get("")
async def get_config():
    """Get the current configuration of the bot."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        # Get full configuration from ConfigManager
        full_config = {}
        if hasattr(bot, 'config') and hasattr(bot.config, 'to_dict'):
            full_config = bot.config.to_dict()
        
        # Create a flattened config for frontend consumption
        config = {
            # Runtime tracked_coins (may differ from config file)
            "tracked_coins": bot.tracked_coins if hasattr(bot, 'tracked_coins') else [],
            # Include other useful config values
            "debug": full_config.get("general", {}).get("debug", False),
            "autostart": full_config.get("general", {}).get("autostart", True),
            "spot_pct": full_config.get("allocation", {}).get("spot_pct", 70),
            "perp_pct": full_config.get("allocation", {}).get("perp_pct", 30),
            "rebalance_threshold": full_config.get("allocation", {}).get("rebalance_threshold", 0.05),
            "refresh_interval_sec": full_config.get("trading", {}).get("refresh_interval_sec", 60),
            # Include full config for reference
            "full_config": full_config
        }
        
        return ConfigResponse(
            success=True,
            message="Configuration retrieved successfully",
            data={"config": config}
        )
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update")
async def update_config(
    updates: Dict[str, Any] = Body(..., description="Configuration updates")
):
    """Update the bot's configuration."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        updated_keys = []
        
        # Validate the updates
        for key, value in updates.items():
            # Don't update the private key or address
            if key in ["private_key", "address"]:
                continue
            
            # Apply the update
            if key == "tracked_coins" and isinstance(value, list):
                bot.tracked_coins = value
                updated_keys.append(key)
            elif hasattr(bot, 'config') and hasattr(bot.config, 'config'):
                # Update the internal config dictionary
                if key in bot.config.config:
                    bot.config.config[key] = value
                    updated_keys.append(key)
        
        return ConfigResponse(
            success=True,
            message="Configuration updated successfully",
            data={"updated_keys": updated_keys}
        )
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tracked-coins")
async def get_tracked_coins():
    """Get the list of tracked coins."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        return ConfigResponse(
            success=True,
            message="Tracked coins retrieved successfully",
            data={"tracked_coins": bot.tracked_coins}
        )
    except Exception as e:
        logger.error(f"Error getting tracked coins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-coin/{coin}")
async def add_tracked_coin(coin: str):
    """Add a coin to the tracked coins list."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        # Check if the coin is already tracked
        if coin in bot.tracked_coins:
            return ConfigResponse(
                success=False,
                message=f"Coin {coin} is already tracked"
            )
        
        # Add the coin to the tracked coins list
        bot.tracked_coins.append(coin)
        
        return ConfigResponse(
            success=True,
            message=f"Added {coin} to tracked coins",
            data={"tracked_coins": bot.tracked_coins}
        )
    except Exception as e:
        logger.error(f"Error adding tracked coin: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/remove-coin/{coin}")
async def remove_tracked_coin(coin: str):
    """Remove a coin from the tracked coins list."""
    if not bot:
        raise HTTPException(status_code=500, detail="Bot instance not initialized")
    
    try:
        # Check if the coin is in the tracked coins list
        if coin not in bot.tracked_coins:
            return ConfigResponse(
                success=False,
                message=f"Coin {coin} is not in the tracked coins list"
            )
        
        # Remove the coin from the tracked coins list
        bot.tracked_coins.remove(coin)
        
        return ConfigResponse(
            success=True,
            message=f"Removed {coin} from tracked coins",
            data={"tracked_coins": bot.tracked_coins}
        )
    except Exception as e:
        logger.error(f"Error removing tracked coin: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 