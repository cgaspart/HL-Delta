"""
Tests for data models
"""

import pytest
from delta_bot.models import SpotMarket, PerpMarket, CoinInfo, PendingDeltaOrder


def test_spot_market_creation():
    """Test SpotMarket dataclass creation"""
    spot = SpotMarket(
        name="UBTC",
        token_id="0x123",
        index=0,
        sz_decimals=5,
        wei_decimals=8,
        is_canonical=True,
        full_name="Universal BTC",
        tick_size=1.0
    )
    
    assert spot.name == "UBTC"
    assert spot.token_id == "0x123"
    assert spot.tick_size == 1.0
    assert spot.position == {}


def test_perp_market_creation():
    """Test PerpMarket dataclass creation"""
    perp = PerpMarket(
        name="BTC",
        sz_decimals=5,
        max_leverage=50,
        index=0,
        tick_size=1.0
    )
    
    assert perp.name == "BTC"
    assert perp.max_leverage == 50
    assert perp.funding_rate is None
    assert perp.yearly_funding_rate is None


def test_coin_info_creation():
    """Test CoinInfo dataclass creation"""
    spot = SpotMarket(
        name="UBTC",
        token_id="0x123",
        index=0,
        sz_decimals=5,
        wei_decimals=8,
        is_canonical=True,
        full_name="Universal BTC",
        tick_size=1.0
    )
    
    perp = PerpMarket(
        name="BTC",
        sz_decimals=5,
        max_leverage=50,
        index=0,
        tick_size=1.0
    )
    
    coin = CoinInfo(name="BTC", spot=spot, perp=perp)
    
    assert coin.name == "BTC"
    assert coin.spot == spot
    assert coin.perp == perp


def test_pending_delta_order_creation():
    """Test PendingDeltaOrder dataclass creation"""
    order = PendingDeltaOrder(coin_name="BTC")
    
    assert order.coin_name == "BTC"
    assert order.spot_oid is None
    assert order.perp_oid is None
    assert order.spot_filled == False
    assert order.perp_filled == False
    assert order.is_closing_position == False
    assert order.max_wait_time == 300


def test_pending_delta_order_with_values():
    """Test PendingDeltaOrder with custom values"""
    order = PendingDeltaOrder(
        coin_name="ETH",
        spot_oid=12345,
        perp_oid=67890,
        is_closing_position=True
    )
    
    assert order.coin_name == "ETH"
    assert order.spot_oid == 12345
    assert order.perp_oid == 67890
    assert order.is_closing_position == True
