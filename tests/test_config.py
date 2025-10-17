"""
Tests for configuration management
"""

import pytest
import os
import json
import tempfile
from delta_bot.config import ConfigManager


def test_config_load():
    """Test loading configuration from file"""
    # Create a temporary config file
    config_data = {
        "general": {
            "debug": False,
            "tracked_coins": ["BTC", "ETH"],
            "autostart": True
        },
        "allocation": {
            "spot_pct": 70,
            "perp_pct": 30,
            "rebalance_threshold": 0.05
        },
        "trading": {
            "refresh_interval_sec": 60
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_path = f.name
    
    try:
        config = ConfigManager(temp_config_path)
        
        assert config.tracked_coins == ["BTC", "ETH"]
        assert config.debug == False
        assert config.autostart == True
        assert config.spot_allocation_pct == 0.7
        assert config.perp_allocation_pct == 0.3
        assert config.rebalance_threshold == 0.05
        assert config.refresh_interval_sec == 60
    finally:
        os.unlink(temp_config_path)


def test_config_get_nested():
    """Test getting nested configuration values"""
    config_data = {
        "general": {
            "debug": True
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_path = f.name
    
    try:
        config = ConfigManager(temp_config_path)
        
        assert config.get("general", "debug") == True
        assert config.get("general", "nonexistent", default=False) == False
        assert config.get("nonexistent", "key", default="default") == "default"
    finally:
        os.unlink(temp_config_path)


def test_config_missing_file():
    """Test handling of missing configuration file"""
    with pytest.raises(FileNotFoundError):
        ConfigManager("nonexistent_config.json")
