"""
Configuration management for the Delta bot
"""

import json
import os
from typing import Dict, Any
from .utils import setup_logger

logger = setup_logger("DeltaBot.Config")


class ConfigManager:
    """Manages bot configuration from config.json and environment variables"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_path} not found")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error parsing JSON in {self.config_path}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            raise
    
    def get(self, *keys, default=None):
        """
        Get a configuration value using dot notation
        
        Example:
            config.get("general", "debug") -> config["general"]["debug"]
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_env(self, env_name: str, required: bool = True) -> str:
        """
        Get an environment variable with validation
        
        Args:
            env_name: Name of the environment variable
            required: Whether the variable is required
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If required variable is not set or has placeholder value
        """
        value = os.getenv(env_name)
        
        if required:
            if not value or value in ["your_private_key_here", "your_eth_address_here"]:
                raise ValueError(
                    f"{env_name} environment variable not set or has default placeholder value"
                )
        
        return value
    
    @property
    def tracked_coins(self):
        """Get list of tracked coins"""
        return self.get("general", "tracked_coins", default=["BTC", "ETH", "HYPE", "USDC"])
    
    @property
    def debug(self):
        """Get debug mode setting"""
        return self.get("general", "debug", default=False)
    
    @property
    def autostart(self):
        """Get autostart setting"""
        return self.get("general", "autostart", default=True)
    
    @property
    def spot_allocation_pct(self):
        """Get spot allocation percentage (as decimal)"""
        return self.get("allocation", "spot_pct", default=70) / 100.0
    
    @property
    def perp_allocation_pct(self):
        """Get perp allocation percentage (as decimal)"""
        return self.get("allocation", "perp_pct", default=30) / 100.0
    
    @property
    def rebalance_threshold(self):
        """Get rebalance threshold"""
        return self.get("allocation", "rebalance_threshold", default=0.05)
    
    @property
    def refresh_interval_sec(self):
        """Get refresh interval in seconds"""
        return self.get("trading", "refresh_interval_sec", default=60)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Return a copy of the configuration as a dictionary
        
        Returns:
            Dictionary copy of the configuration
        """
        return self.config.copy()
