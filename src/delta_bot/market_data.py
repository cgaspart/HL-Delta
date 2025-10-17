"""
Market data operations for the Delta bot
"""

import aiohttp
from typing import Dict, List, Optional
from .utils import setup_logger

logger = setup_logger("DeltaBot.MarketData")


class MarketDataManager:
    """Handles market data fetching and funding rate calculations"""
    
    API_URL = "https://api.hyperliquid.xyz/info"
    
    @staticmethod
    async def fetch_funding_rates() -> Dict[str, str]:
        """
        Fetch current funding rates from Hyperliquid
        
        Returns:
            Dictionary mapping coin names to funding rates
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    MarketDataManager.API_URL,
                    json={"type": "predictedFundings"},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    predicted_fundings = await response.json()
            
            # Process predicted fundings data
            predicted_rates = {}
            for item in predicted_fundings:
                coin = item[0]
                venues = item[1]
                
                for venue in venues:
                    venue_name = venue[0]
                    if venue_name == "HlPerp":  # Hyperliquid Perp
                        predicted_rates[coin] = venue[1].get("fundingRate", "0")
            
            return predicted_rates
            
        except Exception as e:
            logger.error(f"Error fetching funding rates: {e}")
            return {}
    
    @staticmethod
    def calculate_yearly_funding_rates(
        predicted_rates: Dict[str, str],
        coins: Optional[List[str]] = None
    ) -> Dict[str, Optional[float]]:
        """
        Calculate yearly funding rates for specified coins
        
        Args:
            predicted_rates: Dictionary with coin symbols as keys and funding rates as values
            coins: List of coin symbols to calculate yearly rates for
            
        Returns:
            Dictionary with coin symbols as keys and yearly funding rates (%) as values
        """
        if coins is None:
            coins = ["BTC", "ETH", "HYPE"]
        
        # Funding rate is per 1 hour, so multiply by 24 for daily and then by 365 for yearly
        yearly_rates = {}
        for coin in coins:
            if coin in predicted_rates:
                try:
                    # Convert funding rate to float
                    rate = float(predicted_rates[coin])
                    # Calculate yearly rate (24 funding periods per day * 365 days)
                    yearly_rate = rate * 24 * 365
                    # Convert to percentage
                    yearly_percentage = yearly_rate * 100
                    yearly_rates[coin] = yearly_percentage
                except (ValueError, TypeError):
                    yearly_rates[coin] = None
            else:
                yearly_rates[coin] = None  # Coin not found in predicted rates
        
        return yearly_rates
