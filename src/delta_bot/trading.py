"""
Trading operations for the Delta bot
"""

from typing import Dict, Optional, Tuple
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from .models import CoinInfo, PendingDeltaOrder
from .utils import setup_logger

logger = setup_logger("DeltaBot.Trading")


class TradingManager:
    """Handles order execution and tracking"""
    
    def __init__(self, exchange: Exchange, info: Info, coins: Dict[str, CoinInfo]):
        self.exchange = exchange
        self.info = info
        self.coins = coins
    
    def get_spot_pair_name(self, coin_name: str) -> str:
        """
        Get the spot pair name for a coin
        
        Args:
            coin_name: Base coin name (e.g., "BTC", "ETH")
            
        Returns:
            Spot pair name (e.g., "UBTC/USDC", "UETH/USDC")
        """
        if coin_name == "BTC":
            return "UBTC/USDC"
        elif coin_name == "ETH":
            return "UETH/USDC"
        else:
            return f"{coin_name}/USDC"
    
    def round_size(self, coin_name: str, is_spot: bool, size: float) -> float:
        """
        Round size according to market decimals
        
        Args:
            coin_name: Coin name
            is_spot: True for spot market, False for perp
            size: Size to round
            
        Returns:
            Rounded size
        """
        if size <= 0:
            return 0
        
        if coin_name not in self.coins:
            return size
        
        if is_spot:
            if self.coins[coin_name].spot:
                return round(size, self.coins[coin_name].spot.sz_decimals)
        else:
            if self.coins[coin_name].perp:
                return round(size, self.coins[coin_name].perp.sz_decimals)
        
        return size
    
    def round_price(self, coin_name: str, price: float) -> float:
        """
        Round price according to tick size
        
        Args:
            coin_name: Coin name
            price: Price to round
            
        Returns:
            Rounded price
        """
        if coin_name not in self.coins:
            return price
        
        if not self.coins[coin_name].spot:
            return price
        
        tick_size = self.coins[coin_name].spot.tick_size
        if tick_size <= 0:
            return price
        
        return round(price / tick_size) * tick_size
    
    def extract_order_ids(
        self,
        pending_order: PendingDeltaOrder,
        spot_order_result: Optional[Dict],
        perp_order_result: Optional[Dict],
        coin_name: str,
        operation_type: str = ""
    ) -> Tuple[bool, bool, bool]:
        """
        Extract order IDs from order responses and update pending order
        
        Args:
            pending_order: The PendingDeltaOrder object to update
            spot_order_result: The result from the spot order API call
            perp_order_result: The result from the perp order API call
            coin_name: Name of the coin
            operation_type: Type of operation (opening/closing) for logging
        
        Returns:
            Tuple of (has_spot_oid, has_perp_oid, both_filled)
        """
        has_spot_oid = False
        has_perp_oid = False
        
        # Extract order IDs from spot order response
        if spot_order_result and spot_order_result.get('status') == 'ok':
            spot_response = spot_order_result.get('response', {}).get('data', {}).get('statuses', [{}])[0]
            if 'filled' in spot_response:
                pending_order.spot_filled = True
                pending_order.spot_oid = int(spot_response['filled']['oid'])
                has_spot_oid = True
                logger.info(f"Spot {operation_type} order for {coin_name} filled immediately with oid: {pending_order.spot_oid}")
            elif 'resting' in spot_response:
                pending_order.spot_oid = int(spot_response['resting']['oid'])
                has_spot_oid = True
                logger.info(f"Spot {operation_type} order for {coin_name} resting with oid: {pending_order.spot_oid}")
        
        # Extract order IDs from perp order response
        if perp_order_result and perp_order_result.get('status') == 'ok':
            perp_response = perp_order_result.get('response', {}).get('data', {}).get('statuses', [{}])[0]
            if 'filled' in perp_response:
                pending_order.perp_filled = True
                pending_order.perp_oid = int(perp_response['filled']['oid'])
                has_perp_oid = True
                logger.info(f"Perp {operation_type} order for {coin_name} filled immediately with oid: {pending_order.perp_oid}")
            elif 'resting' in perp_response:
                pending_order.perp_oid = int(perp_response['resting']['oid'])
                has_perp_oid = True
                logger.info(f"Perp {operation_type} order for {coin_name} resting with oid: {pending_order.perp_oid}")
        
        both_filled = pending_order.spot_filled and pending_order.perp_filled
        
        return has_spot_oid or has_perp_oid, both_filled, has_spot_oid and has_perp_oid
    
    async def place_spot_order(
        self,
        coin_name: str,
        is_buy: bool,
        size: float,
        price: float
    ) -> Optional[Dict]:
        """
        Place a spot order
        
        Args:
            coin_name: Coin name
            is_buy: True for buy, False for sell
            size: Order size
            price: Limit price
            
        Returns:
            Order result dictionary or None on error
        """
        try:
            spot_pair = self.get_spot_pair_name(coin_name)
            result = self.exchange.order(
                spot_pair,
                is_buy,
                size,
                price,
                {"limit": {"tif": "Gtc"}}
            )
            logger.info(f"Spot {'buy' if is_buy else 'sell'} order for {coin_name}: {size} @ {price} - Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error placing spot order for {coin_name}: {e}")
            return None
    
    async def place_perp_order(
        self,
        coin_name: str,
        is_buy: bool,
        size: float,
        price: float
    ) -> Optional[Dict]:
        """
        Place a perp order
        
        Args:
            coin_name: Coin name
            is_buy: True for buy/long, False for sell/short
            size: Order size (always positive)
            price: Limit price
            
        Returns:
            Order result dictionary or None on error
        """
        try:
            result = self.exchange.order(
                coin_name,
                is_buy,
                size,
                price,
                {"limit": {"tif": "Gtc"}}
            )
            logger.info(f"Perp {'buy' if is_buy else 'sell'} order for {coin_name}: {size} @ {price} - Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error placing perp order for {coin_name}: {e}")
            return None
    
    async def cancel_order(self, coin_name: str, oid: int, is_spot: bool = False) -> bool:
        """
        Cancel an order
        
        Args:
            coin_name: Coin name
            oid: Order ID
            is_spot: True if spot order, False if perp order
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if is_spot:
                spot_pair = self.get_spot_pair_name(coin_name)
                result = self.exchange.cancel(spot_pair, oid)
            else:
                result = self.exchange.cancel(coin_name, oid)
            
            logger.info(f"Cancelled {'spot' if is_spot else 'perp'} order {oid} for {coin_name}: {result}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling {'spot' if is_spot else 'perp'} order {oid} for {coin_name}: {e}")
            return False
    
    def check_order_status(self, address: str, oid: int) -> Optional[Dict]:
        """
        Check the status of an order
        
        Args:
            address: User address
            oid: Order ID
            
        Returns:
            Order status dictionary or None
        """
        try:
            return self.info.query_order_by_oid(address, oid)
        except Exception as e:
            logger.error(f"Error checking order status for oid {oid}: {e}")
            return None
