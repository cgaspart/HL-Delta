"""
HL-Delta: Automated delta-neutral trading system for Hyperliquid
"""

__version__ = "2.0.0"
__author__ = "HyperVault Team"

from .bot import DeltaBot
from .models import SpotMarket, PerpMarket, CoinInfo, PendingDeltaOrder

__all__ = [
    "DeltaBot",
    "SpotMarket",
    "PerpMarket",
    "CoinInfo",
    "PendingDeltaOrder",
]
