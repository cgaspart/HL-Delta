"""
Tests for market data operations
"""

import pytest
from delta_bot.market_data import MarketDataManager


def test_calculate_yearly_funding_rates():
    """Test yearly funding rate calculation"""
    predicted_rates = {
        "BTC": "0.0001",  # 0.01% per hour
        "ETH": "0.0002",  # 0.02% per hour
        "HYPE": "0.0005"  # 0.05% per hour
    }
    
    yearly_rates = MarketDataManager.calculate_yearly_funding_rates(
        predicted_rates,
        ["BTC", "ETH", "HYPE"]
    )
    
    # 0.0001 * 24 * 365 * 100 = 87.6%
    assert abs(yearly_rates["BTC"] - 87.6) < 0.1
    # 0.0002 * 24 * 365 * 100 = 175.2%
    assert abs(yearly_rates["ETH"] - 175.2) < 0.1
    # 0.0005 * 24 * 365 * 100 = 438%
    assert abs(yearly_rates["HYPE"] - 438.0) < 0.1


def test_calculate_yearly_funding_rates_missing_coin():
    """Test handling of missing coins in funding rates"""
    predicted_rates = {
        "BTC": "0.0001"
    }
    
    yearly_rates = MarketDataManager.calculate_yearly_funding_rates(
        predicted_rates,
        ["BTC", "ETH"]
    )
    
    assert yearly_rates["BTC"] is not None
    assert yearly_rates["ETH"] is None


def test_calculate_yearly_funding_rates_invalid_value():
    """Test handling of invalid funding rate values"""
    predicted_rates = {
        "BTC": "invalid"
    }
    
    yearly_rates = MarketDataManager.calculate_yearly_funding_rates(
        predicted_rates,
        ["BTC"]
    )
    
    assert yearly_rates["BTC"] is None


def test_calculate_yearly_funding_rates_zero():
    """Test calculation with zero funding rate"""
    predicted_rates = {
        "BTC": "0"
    }
    
    yearly_rates = MarketDataManager.calculate_yearly_funding_rates(
        predicted_rates,
        ["BTC"]
    )
    
    assert yearly_rates["BTC"] == 0.0


def test_calculate_yearly_funding_rates_negative():
    """Test calculation with negative funding rate"""
    predicted_rates = {
        "BTC": "-0.0001"
    }
    
    yearly_rates = MarketDataManager.calculate_yearly_funding_rates(
        predicted_rates,
        ["BTC"]
    )
    
    # -0.0001 * 24 * 365 * 100 = -87.6%
    assert abs(yearly_rates["BTC"] - (-87.6)) < 0.1
