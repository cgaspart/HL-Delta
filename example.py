#!/usr/bin/env python3
"""
Example script showing how to use the DeltaBot class with config.json
"""

import asyncio
import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from delta_bot import DeltaBot
from delta_bot.utils import setup_logger

logger = setup_logger("Example")

# Ensure we have environment variables set
if not os.getenv("HYPERLIQUID_PRIVATE_KEY") or not os.getenv("HYPERLIQUID_ADDRESS"):
    print("Error: Environment variables HYPERLIQUID_PRIVATE_KEY and HYPERLIQUID_ADDRESS must be set")
    print("Example:")
    print("export HYPERLIQUID_PRIVATE_KEY=your_private_key_here")
    print("export HYPERLIQUID_ADDRESS=your_eth_address_here")
    sys.exit(1)

async def main():
    try:
        # Create DeltaBot instance with config.json
        delta = DeltaBot(config_path="config.json")
        
        # Display account and position information
        delta.display_position_info()
        
        # Get funding rates for tracked coins
        print("\nFetching current funding rates...")
        await delta.update_funding_rates()
        
        print("\nCurrent Funding Rates:")
        for coin_name in delta.config.tracked_coins:
            if coin_name != "USDC" and coin_name in delta.coins:
                coin = delta.coins[coin_name]
                if coin.perp and coin.perp.yearly_funding_rate is not None:
                    print(f"{coin_name}: {coin.perp.yearly_funding_rate:.4f}% APR")
                else:
                    print(f"{coin_name}: N/A")
        
        # Check for the best funding rate
        best_coin = delta.get_best_funding_rate_coin()
        if best_coin:
            print(f"\nBest funding rate coin: {best_coin} ({delta.coins[best_coin].perp.yearly_funding_rate:.4f}% APR)")
        
        # Example: Check allocation
        allocation_ok = delta.check_allocation()
        if not allocation_ok:
            print(f"\nAllocation mismatch from target {delta.config.spot_allocation_pct*100:.0f}% spot / {delta.config.perp_allocation_pct*100:.0f}% perp ratio")
        
        print("\nExample completed successfully")
        
    except Exception as e:
        logger.error(f"Error running example: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}") 