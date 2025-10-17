"""
Data models for the Delta bot
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class SpotMarket:
    """Represents a spot market on Hyperliquid"""
    name: str
    token_id: str
    index: int
    sz_decimals: int
    wei_decimals: int
    is_canonical: bool
    full_name: str
    evm_contract: Optional[Dict] = None
    deployer_trading_fee_share: str = "0.0"
    position: Dict[str, Any] = field(default_factory=dict)
    tick_size: float = 0


@dataclass
class PerpMarket:
    """Represents a perpetual market on Hyperliquid"""
    name: str
    sz_decimals: int
    max_leverage: int
    index: int
    position: Dict[str, Any] = field(default_factory=dict)
    funding_rate: Optional[float] = None
    yearly_funding_rate: Optional[float] = None
    tick_size: float = 0


@dataclass
class CoinInfo:
    """Container for both spot and perp market information for a coin"""
    name: str
    spot: Optional[SpotMarket] = None
    perp: Optional[PerpMarket] = None


@dataclass
class PendingDeltaOrder:
    """Tracks pending delta-neutral orders"""
    coin_name: str
    spot_oid: Optional[int] = None
    perp_oid: Optional[int] = None
    creation_time: float = field(default_factory=time.time)
    last_check_time: float = field(default_factory=time.time)
    spot_filled: bool = False
    perp_filled: bool = False
    max_wait_time: int = 300  # 5 minutes in seconds
    is_closing_position: bool = False  # Flag to indicate if this is for closing a position
