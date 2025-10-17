"""
Position management for the Delta bot
"""

import time
import asyncio
from typing import Dict, List, Tuple, Optional
from hyperliquid.info import Info
from .models import CoinInfo, PendingDeltaOrder
from .trading import TradingManager
from .utils import setup_logger, Colors

logger = setup_logger("DeltaBot.Positions")


class PositionManager:
    """Manages delta-neutral positions and pending orders"""
    
    def __init__(
        self,
        info: Info,
        trading_manager: TradingManager,
        coins: Dict[str, CoinInfo],
        address: str
    ):
        self.info = info
        self.trading = trading_manager
        self.coins = coins
        self.address = address
        self.pending_orders: List[PendingDeltaOrder] = []
    
    def get_mid_price(self, coin_name: str) -> float:
        """
        Get the mid price for a coin
        
        Args:
            coin_name: Coin name
            
        Returns:
            Mid price or 0 if not found
        """
        try:
            mid_prices = self.info.all_mids()
            return float(mid_prices.get(coin_name, 0))
        except Exception as e:
            logger.error(f"Error getting mid price for {coin_name}: {e}")
            return 0
    
    def get_usdc_balance(self) -> float:
        """
        Get available USDC balance in spot account
        
        Returns:
            USDC balance
        """
        try:
            spot_user_state = self.info.spot_user_state(self.address)
            for balance in spot_user_state.get("balances", []):
                if balance["coin"] == "USDC":
                    return float(balance["total"])
            return 0
        except Exception as e:
            logger.error(f"Error getting USDC balance: {e}")
            return 0
    
    def has_delta_neutral_position(
        self,
        coin_name: str,
        error_margin: float = 0.05
    ) -> Tuple[bool, float, float, float]:
        """
        Check if a coin has a delta-neutral position
        
        Args:
            coin_name: Coin name
            error_margin: Acceptable error margin (default 5%)
            
        Returns:
            Tuple of (is_delta_neutral, perp_size, spot_size, diff_percentage)
        """
        if coin_name not in self.coins:
            logger.warning(f"Coin {coin_name} not found in tracked coins")
            return False, 0, 0, 0
        
        coin_info = self.coins[coin_name]
        
        if not (coin_info.perp and coin_info.spot):
            logger.debug(f"{coin_name} doesn't have both perp and spot markets")
            return False, 0, 0, 0
        
        perp_size = 0
        if coin_info.perp.position:
            perp_size = coin_info.perp.position.get("size", 0)
        
        spot_size = 0
        if coin_info.spot.position:
            spot_size = coin_info.spot.position.get("total", 0)
        
        if perp_size == 0 or spot_size == 0:
            return False, perp_size, spot_size, 0
        
        is_proper_direction = perp_size < 0 and spot_size > 0
        
        abs_perp_size = abs(perp_size)
        size_diff = abs(abs_perp_size - spot_size)
        
        larger_size = max(abs_perp_size, spot_size)
        diff_percentage = (size_diff / larger_size) * 100 if larger_size > 0 else 0
        
        is_within_margin = diff_percentage <= (error_margin * 100)
        
        is_delta_neutral = is_proper_direction and is_within_margin
        
        return is_delta_neutral, perp_size, spot_size, diff_percentage
    
    def calculate_optimal_spot_size(self, coin_name: str) -> float:
        """
        Calculate optimal spot size based on available USDC
        
        Args:
            coin_name: Coin name
            
        Returns:
            Optimal spot size
        """
        spot_price = self.get_mid_price(coin_name)
        usdc_balance = self.get_usdc_balance()
        
        # Use only up to 90% of available USDC to account for fees and price fluctuations
        available_usdc = usdc_balance * 0.9
        
        # Ensure we have sufficient USDC (at least $10 worth)
        if available_usdc < 10:
            logger.warning(f"Insufficient USDC balance for spot purchase: ${available_usdc:.2f}")
            return 0
        
        # Calculate size based on available USDC and current price
        size = available_usdc / spot_price if spot_price > 0 else 0
        
        # Set minimum size threshold (e.g. $10 worth)
        min_size_value = 10 / spot_price if spot_price > 0 else 0
        
        if size < min_size_value:
            logger.warning(f"Calculated spot size too small: {size} (min: {min_size_value})")
            return 0
        
        rounded_size = self.trading.round_size(coin_name, True, size)
        
        logger.info(f"Calculated optimal spot size for {coin_name}: {size} -> rounded to {rounded_size} (USDC: ${available_usdc:.2f}, price: ${spot_price:.2f})")
        
        return rounded_size
    
    async def create_delta_position(self, coin_name: str) -> bool:
        """
        Create a delta-neutral position for a coin
        
        Args:
            coin_name: Coin name
            
        Returns:
            True if successful, False otherwise
        """
        if coin_name not in self.coins:
            logger.warning(f"Coin {coin_name} not found in tracked coins")
            return False
        
        coin_info = self.coins[coin_name]
        
        if not (coin_info.perp and coin_info.spot):
            logger.warning(f"{coin_name} doesn't have both perp and spot markets")
            return False
        
        # Check if we already have a delta-neutral position for this coin
        is_delta_neutral, perp_size, spot_size, _ = self.has_delta_neutral_position(coin_name)
        if is_delta_neutral:
            logger.info(f"Already have a delta-neutral position for {coin_name} - perp: {perp_size}, spot: {spot_size}")
            return True
        
        try:
            price = self.get_mid_price(coin_name)
            if price <= 0:
                logger.error(f"Invalid price for {coin_name}: {price}")
                return False
            
            # Get optimal sizes for spot and perp
            spot_size = self.calculate_optimal_spot_size(coin_name)
            if spot_size <= 0:
                logger.error(f"Calculated spot size for {coin_name} is not positive: {spot_size}")
                return False
            
            perp_size = spot_size  # For delta-neutral, perp size equals spot size
            
            # Validate the sizes after rounding
            if spot_size <= 0 or perp_size <= 0:
                logger.error(f"Invalid position size after rounding for {coin_name}: spot={spot_size}, perp={perp_size}")
                return False
            
            # Calculate minimum size based on $10 value
            min_size_value = 10 / price
            if spot_size < min_size_value:
                logger.warning(f"Calculated position size for {coin_name} is too small: {spot_size} < {min_size_value}")
                logger.warning(f"Current price: ${price}, minimum position value: $10")
                return False
            
            # Ensure we have enough USDC for this purchase
            required_usdc = spot_size * price
            available_usdc = self.get_usdc_balance()
            if required_usdc > available_usdc * 0.95:  # Leave 5% buffer
                logger.warning(f"Insufficient USDC for {coin_name} position: need ${required_usdc:.2f}, have ${available_usdc:.2f}")
                return False
            
            tick_size = coin_info.spot.tick_size
            spot_limit_price = self.trading.round_price(coin_name, price + tick_size)
            perp_limit_price = self.trading.round_price(coin_name, price - tick_size)
            
            # Create a new pending order to track
            pending_order = PendingDeltaOrder(coin_name=coin_name, is_closing_position=False)
            
            logger.info(f"Creating spot buy limit order for {coin_name}: {spot_size} @ {spot_limit_price}")
            spot_order_result = await self.trading.place_spot_order(coin_name, True, spot_size, spot_limit_price)
            
            logger.info(f"Creating perp short limit order for {coin_name}: {perp_size} @ {perp_limit_price}")
            perp_order_result = await self.trading.place_perp_order(coin_name, False, perp_size, perp_limit_price)
            
            # Extract and track order IDs
            has_orders, both_filled, _ = self.trading.extract_order_ids(
                pending_order,
                spot_order_result,
                perp_order_result,
                coin_name,
                "opening"
            )
            
            if has_orders and not both_filled:
                self.pending_orders.append(pending_order)
                logger.info(f"Added pending opening position for {coin_name} to tracking")
                return True
            elif both_filled:
                logger.info(f"Both opening orders for {coin_name} filled immediately")
                return True
            else:
                logger.warning(f"Failed to create or track opening orders for {coin_name}")
                return False
            
        except Exception as e:
            logger.error(f"Error creating delta-neutral position for {coin_name}: {e}")
            return False
    
    def close_delta_position(self, coin_name: str) -> bool:
        """
        Close a delta-neutral position for a coin
        
        Args:
            coin_name: Coin name
            
        Returns:
            True if successful, False otherwise
        """
        if coin_name not in self.coins:
            logger.warning(f"Coin {coin_name} not found in tracked coins")
            return False
        
        coin_info = self.coins[coin_name]
        
        if not (coin_info.perp and coin_info.spot):
            logger.warning(f"{coin_name} doesn't have both perp and spot markets")
            return False
        
        try:
            # Check if we have positions to close
            is_delta_neutral, perp_size, spot_size, _ = self.has_delta_neutral_position(coin_name)
            
            if not is_delta_neutral:
                logger.warning(f"No delta-neutral position for {coin_name} to close")
                return False
            
            price = self.get_mid_price(coin_name)
            if price <= 0:
                logger.error(f"Invalid price for {coin_name}: {price}")
                return False
            
            # For closing, we reverse the orders:
            # - Sell the spot position
            # - Buy back (cover) the short perp position
            
            tick_size = coin_info.spot.tick_size
            spot_limit_price = self.trading.round_price(coin_name, price - tick_size)  # Sell slightly below market
            perp_limit_price = self.trading.round_price(coin_name, price + tick_size)  # Buy slightly above market
            
            # Create a new pending order to track
            pending_order = PendingDeltaOrder(coin_name=coin_name, is_closing_position=True)
            spot_order_result = None
            perp_order_result = None
            
            # For spot, we need to sell what we have
            if spot_size > 0:
                # Get actual available balance (total minus any amount on hold)
                available_spot_size = spot_size
                if coin_info.spot.position and "hold" in coin_info.spot.position:
                    available_spot_size = spot_size - coin_info.spot.position["hold"]
                
                # Ensure positive size and proper rounding
                if available_spot_size <= 0:
                    logger.warning(f"No available balance for {coin_name} - total: {spot_size}, hold: {coin_info.spot.position.get('hold', 0)}")
                    return False
                
                # Round to the proper number of decimals for this spot market
                rounded_spot_size = self.trading.round_size(coin_name, True, available_spot_size)
                
                logger.info(f"Creating spot sell limit order for {coin_name}: {rounded_spot_size} @ {spot_limit_price}")
                spot_order_result = asyncio.create_task(
                    self.trading.place_spot_order(coin_name, False, rounded_spot_size, spot_limit_price)
                )
            
            # For perp, we need to buy back our short position
            if perp_size < 0:
                # Convert negative size to positive for buy order
                buy_size = abs(perp_size)
                logger.info(f"Creating perp buy limit order to close short for {coin_name}: {buy_size} @ {perp_limit_price}")
                perp_order_result = asyncio.create_task(
                    self.trading.place_perp_order(coin_name, True, buy_size, perp_limit_price)
                )
            
            # Wait for both orders to complete if they were created
            if spot_order_result:
                spot_order_result = asyncio.run(spot_order_result)
            if perp_order_result:
                perp_order_result = asyncio.run(perp_order_result)
            
            # Extract and track order IDs
            has_orders, both_filled, _ = self.trading.extract_order_ids(
                pending_order,
                spot_order_result,
                perp_order_result,
                coin_name,
                "closing"
            )
            
            if has_orders and not both_filled:
                self.pending_orders.append(pending_order)
                logger.info(f"Added pending closing position for {coin_name} to tracking")
                return True
            elif both_filled:
                logger.info(f"Both closing orders for {coin_name} filled immediately")
                return True
            else:
                logger.warning(f"Failed to create or track closing orders for {coin_name}")
                return False
            
        except Exception as e:
            logger.error(f"Error closing delta-neutral position for {coin_name}: {e}")
            return False
    
    async def check_pending_orders(self):
        """Check the status of all pending orders and handle accordingly"""
        if not self.pending_orders:
            return
        
        current_time = time.time()
        orders_to_remove = []
        
        for pending_order in self.pending_orders:
            # Skip if checked recently (less than 30 seconds ago)
            if current_time - pending_order.last_check_time < 30:
                continue
            
            pending_order.last_check_time = current_time
            
            operation_type = "closing" if pending_order.is_closing_position else "opening"
            logger.info(f"Checking pending {operation_type} delta position for {pending_order.coin_name}")
            
            # Check if both orders are already filled
            if pending_order.spot_filled and pending_order.perp_filled:
                logger.info(f"Both {operation_type} orders for {pending_order.coin_name} are filled, removing from pending")
                orders_to_remove.append(pending_order)
                continue
            
            # Check if we've waited too long
            if current_time - pending_order.creation_time > pending_order.max_wait_time:
                logger.warning(f"{operation_type.capitalize()} orders for {pending_order.coin_name} have been pending for too long, cancelling")
                
                if not pending_order.spot_filled and pending_order.spot_oid:
                    await self.trading.cancel_order(pending_order.coin_name, pending_order.spot_oid, is_spot=True)
                
                if not pending_order.perp_filled and pending_order.perp_oid:
                    await self.trading.cancel_order(pending_order.coin_name, pending_order.perp_oid, is_spot=False)
                
                orders_to_remove.append(pending_order)
                
                # Only try to recreate a delta position if we were opening, not closing
                if not pending_order.is_closing_position:
                    logger.info(f"Recreating delta position for {pending_order.coin_name}")
                    await self.create_delta_position(pending_order.coin_name)
                
                continue
            
            # Check current order status from exchange
            try:
                # Check spot order status if not already filled
                if not pending_order.spot_filled and pending_order.spot_oid:
                    spot_order_response = self.trading.check_order_status(self.address, pending_order.spot_oid)
                    
                    if spot_order_response:
                        if spot_order_response.get('status') == 'order':
                            order_data = spot_order_response.get('order', {})
                            if order_data.get('status') != 'open':
                                logger.info(f"Spot {operation_type} order for {pending_order.coin_name} is no longer open, marking as filled")
                                pending_order.spot_filled = True
                        else:
                            logger.info(f"Spot {operation_type} order for {pending_order.coin_name} not found, marking as filled")
                            pending_order.spot_filled = True
                
                # Check perp order status if not already filled
                if not pending_order.perp_filled and pending_order.perp_oid:
                    perp_order_response = self.trading.check_order_status(self.address, pending_order.perp_oid)
                    
                    if perp_order_response:
                        if perp_order_response.get('status') == 'order':
                            order_data = perp_order_response.get('order', {})
                            if order_data.get('status') != 'open':
                                logger.info(f"Perp {operation_type} order for {pending_order.coin_name} is no longer open, marking as filled")
                                pending_order.perp_filled = True
                        else:
                            logger.info(f"Perp {operation_type} order for {pending_order.coin_name} not found, marking as filled")
                            pending_order.perp_filled = True
                
                # If both are now filled, remove from pending
                if pending_order.spot_filled and pending_order.perp_filled:
                    logger.info(f"Both {operation_type} orders for {pending_order.coin_name} are now filled, removing from pending")
                    orders_to_remove.append(pending_order)
                
            except Exception as e:
                logger.error(f"Error checking {operation_type} order status for {pending_order.coin_name}: {e}")
        
        # Remove processed orders
        for order in orders_to_remove:
            self.pending_orders.remove(order)
