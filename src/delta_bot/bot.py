"""
Main Delta bot class
"""

import asyncio
import time
from typing import Dict, Optional
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants
import eth_account
from eth_account.signers.local import LocalAccount

from .config import ConfigManager
from .models import CoinInfo, SpotMarket, PerpMarket
from .market_data import MarketDataManager
from .trading import TradingManager
from .positions import PositionManager
from .utils import setup_logger, Colors

logger = setup_logger("DeltaBot")


class DeltaBot:
    """Main Delta bot for automated delta-neutral trading"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the Delta bot
        
        Args:
            config_path: Path to configuration file
        """
        self.config = ConfigManager(config_path)
        self._is_running = False
        self.tracked_coins = self.config.tracked_coins.copy()  # Mutable list for runtime updates
        
        # Set debug mode
        if self.config.debug:
            logger.setLevel("DEBUG")
            logger.debug("Debug mode enabled")
        
        # Initialize Hyperliquid clients
        self._init_hyperliquid_clients()
        
        # Initialize coins and markets
        self.coins: Dict[str, CoinInfo] = {}
        self._load_markets()
        
        # Initialize account state
        self._load_account_state()
        
        # Initialize managers
        self.market_data = MarketDataManager()
        self.trading = TradingManager(self.exchange, self.info, self.coins)
        self.positions = PositionManager(self.info, self.trading, self.coins, self.address)
        
        logger.info(f"Initialized with account: {self.address[:8]}...")
        logger.info(f"Total account value: ${self.account_value:.2f}")
    
    def _init_hyperliquid_clients(self):
        """Initialize Hyperliquid exchange and info clients"""
        try:
            private_key = self.config.get_env("HYPERLIQUID_PRIVATE_KEY")
            self.address = self.config.get_env("HYPERLIQUID_ADDRESS")
            
            self.account: LocalAccount = eth_account.Account.from_key(private_key)
            self.exchange = Exchange(
                self.account,
                constants.MAINNET_API_URL,
                vault_address=self.address
            )
            self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
            self.api_url = constants.MAINNET_API_URL
            
        except Exception as e:
            logger.error(f"Failed to initialize Hyperliquid clients: {e}")
            raise RuntimeError("Client initialization failed") from e
    
    def _load_markets(self):
        """Load spot and perp market metadata"""
        try:
            # Load spot markets
            spot_meta = self.info.spot_meta()
            spot_coins = spot_meta["tokens"]
            
            # Load perp markets
            perp_meta = self.info.meta()
            perp_coins = perp_meta["universe"]
            
            # Initialize tracked coins
            for coin_name in self.tracked_coins:
                self.coins[coin_name] = CoinInfo(name=coin_name)
                
                # Match spot markets
                for spot_coin in spot_coins:
                    if self._is_matching_spot_coin(coin_name, spot_coin):
                        tick_size = self._get_tick_size_for_coin(coin_name)
                        self.coins[coin_name].spot = SpotMarket(
                            name=spot_coin["name"],
                            token_id=spot_coin["tokenId"],
                            index=spot_coin["index"],
                            sz_decimals=spot_coin["szDecimals"],
                            wei_decimals=spot_coin["weiDecimals"],
                            is_canonical=spot_coin["isCanonical"],
                            full_name=spot_coin["fullName"],
                            evm_contract=spot_coin.get("evmContract"),
                            deployer_trading_fee_share=spot_coin["deployerTradingFeeShare"],
                            tick_size=tick_size
                        )
                        break
                
                # Match perp markets
                for perp_coin in perp_coins:
                    if perp_coin["name"] == coin_name:
                        tick_size = self.coins[coin_name].spot.tick_size if self.coins[coin_name].spot else 0
                        self.coins[coin_name].perp = PerpMarket(
                            name=perp_coin["name"],
                            sz_decimals=perp_coin["szDecimals"],
                            max_leverage=perp_coin["maxLeverage"],
                            index=perp_coins.index(perp_coin),
                            tick_size=tick_size
                        )
                        break
            
            logger.info(f"Loaded market data for {len(self.coins)} coins")
            
        except Exception as e:
            logger.error(f"Failed to load markets: {e}")
            raise
    
    def _is_matching_spot_coin(self, coin_name: str, spot_coin: dict) -> bool:
        """Check if a spot coin matches the tracked coin name"""
        if coin_name == "BTC" and spot_coin["name"] == "UBTC":
            return True
        elif coin_name == "ETH" and spot_coin["name"] == "UETH":
            return True
        elif coin_name == spot_coin["name"]:
            return True
        return False
    
    def _get_tick_size_for_coin(self, coin_name: str) -> float:
        """Get the tick size for a coin"""
        if coin_name == "BTC":
            return 1.0
        elif coin_name == "ETH":
            return 0.1
        else:
            return 0.001
    
    def _load_account_state(self):
        """Load account state and positions"""
        try:
            self.user_state = self.info.user_state(self.address)
            self.spot_user_state = self.info.spot_user_state(self.address)
            
            # Extract account values
            self.account_balance = float(self.user_state['crossMarginSummary'].get('accountValue', 0))
            self.margin_summary = self.user_state["marginSummary"]
            self.total_raw_usd = float(self.margin_summary["totalRawUsd"])
            self.account_value = float(self.margin_summary["accountValue"])
            self.total_margin_used = float(self.margin_summary["totalMarginUsed"])
            self.perp_user_state = self.account_balance
            
            # Load perp positions
            for position in self.user_state.get("assetPositions", []):
                if position["type"] == "oneWay" and "position" in position:
                    pos = position["position"]
                    coin_name = pos["coin"]
                    if coin_name in self.coins and self.coins[coin_name].perp:
                        self.coins[coin_name].perp.position = {
                            "size": float(pos["szi"]),
                            "entry_price": float(pos["entryPx"]),
                            "position_value": float(pos["positionValue"]),
                            "unrealized_pnl": float(pos["unrealizedPnl"]),
                            "leverage": pos["leverage"]["value"],
                            "liquidation_price": float(pos["liquidationPx"]),
                            "cum_funding": pos["cumFunding"]["allTime"]
                        }
            
            # Load spot positions
            for balance in self.spot_user_state.get("balances", []):
                if float(balance["total"]) > 0:
                    coin_name = balance["coin"]
                    
                    # Map UBTC/UETH to BTC/ETH
                    if coin_name == "UBTC":
                        coin_name = "BTC"
                    elif coin_name == "UETH":
                        coin_name = "ETH"
                    
                    if coin_name in self.coins and self.coins[coin_name].spot:
                        self.coins[coin_name].spot.position = {
                            "total": float(balance["total"]),
                            "hold": float(balance["hold"]),
                            "entry_ntl": float(balance["entryNtl"])
                        }
            
        except Exception as e:
            logger.error(f"Failed to load account state: {e}")
            raise
    
    def refresh_positions(self):
        """Refresh position data from exchange"""
        try:
            self._load_account_state()
            logger.info(f"{Colors.GREEN}Successfully refreshed position data{Colors.RESET}")
        except Exception as e:
            logger.error(f"{Colors.RED}Error refreshing position data: {e}{Colors.RESET}")
    
    def get_total_spot_account_value(self) -> float:
        """Calculate total spot account value including USDC and all positions"""
        total_spot_value = self.positions.get_usdc_balance()
        for coin_name, coin_info in self.coins.items():
            if coin_info.spot and coin_info.spot.position and "total" in coin_info.spot.position:
                price = self.positions.get_mid_price(coin_name)
                total_spot_value += coin_info.spot.position["total"] * price
        return total_spot_value
    
    def get_spot_perp_ratio(self) -> float:
        """Calculate spot/perp allocation ratio"""
        spot_value = self.get_total_spot_account_value()
        perp_value = self.perp_user_state
        total = spot_value + perp_value
        return spot_value / total if total > 0 else 0
    
    def check_allocation(self) -> bool:
        """
        Check if portfolio allocation is within target ratio
        
        Returns:
            True if within threshold, False otherwise
        """
        ratio = self.get_spot_perp_ratio()
        lower_bound = self.config.spot_allocation_pct - self.config.rebalance_threshold
        upper_bound = self.config.spot_allocation_pct + self.config.rebalance_threshold
        
        if ratio < lower_bound:
            spot_value = self.get_total_spot_account_value()
            perp_value = self.perp_user_state
            amount_to_transfer = (perp_value * self.config.spot_allocation_pct - spot_value * self.config.perp_allocation_pct)
            logger.info(f"Allocation mismatch: {ratio:.2f} (target: {self.config.spot_allocation_pct:.2f})")
            logger.info(f"Recommended transfer from perp to spot: ${amount_to_transfer:.2f}")
            return False
        elif ratio > upper_bound:
            spot_value = self.get_total_spot_account_value()
            perp_value = self.perp_user_state
            amount_to_transfer = (spot_value * self.config.perp_allocation_pct - perp_value * self.config.spot_allocation_pct)
            logger.info(f"Allocation mismatch: {ratio:.2f} (target: {self.config.spot_allocation_pct:.2f})")
            logger.info(f"Recommended transfer from spot to perp: ${amount_to_transfer:.2f}")
            return False
        
        return True
    
    def get_best_funding_rate_coin(self) -> Optional[str]:
        """
        Find the coin with the best yearly funding rate
        
        Returns:
            Coin name with best rate, or None
        """
        best_rate = 0
        best_coin = None
        for coin_name, coin_info in self.coins.items():
            if coin_info.perp and coin_info.perp.yearly_funding_rate:
                if coin_info.perp.yearly_funding_rate > best_rate:
                    best_rate = coin_info.perp.yearly_funding_rate
                    best_coin = coin_name
        return best_coin
    
    async def update_funding_rates(self):
        """Fetch and update funding rates for all tracked coins"""
        try:
            funding_rates = await self.market_data.fetch_funding_rates()
            yearly_rates = self.market_data.calculate_yearly_funding_rates(
                funding_rates,
                self.tracked_coins
            )
            
            # Update coin data
            for coin_name, rate in funding_rates.items():
                if coin_name in self.coins and self.coins[coin_name].perp:
                    self.coins[coin_name].perp.funding_rate = float(rate)
            
            for coin_name, rate in yearly_rates.items():
                if coin_name in self.coins and self.coins[coin_name].perp:
                    self.coins[coin_name].perp.yearly_funding_rate = rate
            
            logger.info("Updated funding rates for all tracked coins")
            
        except Exception as e:
            logger.error(f"Error updating funding rates: {e}")
    
    def display_position_info(self):
        """Display detailed information about tracked coins and positions"""
        logger.info(f"\n{Colors.BOLD}Tracked Coins Information:{Colors.RESET}")
        
        for coin_name, coin_info in self.coins.items():
            if coin_name == "USDC":
                continue
            
            logger.info(f"\n{Colors.BOLD}{Colors.YELLOW}{coin_name} Markets:{Colors.RESET}")
            
            is_delta_neutral, perp_size, spot_size, diff_percentage = self.positions.has_delta_neutral_position(coin_name)
            
            status_color = Colors.GREEN if is_delta_neutral else Colors.RED
            status_text = "✅ DELTA NEUTRAL" if is_delta_neutral else "❌ NOT DELTA NEUTRAL"
            logger.info(f"  Delta Status: {status_color}{status_text}{Colors.RESET}")
            
            if perp_size != 0 or spot_size != 0:
                logger.info(f"    Perp Size: {Colors.BLUE}{perp_size:.4f}{Colors.RESET}")
                logger.info(f"    Spot Size: {Colors.GREEN}{spot_size:.4f}{Colors.RESET}")
                diff_color = Colors.GREEN if diff_percentage < 5 else Colors.YELLOW if diff_percentage < 10 else Colors.RED
                logger.info(f"    Difference: {diff_color}{diff_percentage:.2f}%{Colors.RESET}")
            
            if coin_info.perp and coin_info.perp.yearly_funding_rate is not None:
                rate = coin_info.perp.yearly_funding_rate
                rate_color = Colors.RED
                if rate >= 20:
                    rate_color = Colors.GREEN + Colors.BOLD
                elif rate >= 10:
                    rate_color = Colors.GREEN
                elif rate >= 5:
                    rate_color = Colors.YELLOW
                logger.info(f"    Yearly Funding Rate: {rate_color}{rate:.4f}%{Colors.RESET}")
        
        ratio = self.get_spot_perp_ratio()
        ratio_color = Colors.GREEN if 0.665 <= ratio <= 0.735 else Colors.YELLOW if 0.6 <= ratio <= 0.8 else Colors.RED
        logger.info(f"\nSpot/Perp Ratio: {ratio_color}{ratio:.4f}{Colors.RESET} (target: {Colors.GREEN}{self.config.spot_allocation_pct:.2f}{Colors.RESET})")
        
        best_coin = self.get_best_funding_rate_coin()
        if best_coin:
            rate = self.coins[best_coin].perp.yearly_funding_rate
            rate_color = Colors.RED
            if rate >= 20:
                rate_color = Colors.GREEN + Colors.BOLD
            elif rate >= 10:
                rate_color = Colors.GREEN
            elif rate >= 5:
                rate_color = Colors.YELLOW
            logger.info(f"Best funding rate coin: {Colors.YELLOW}{best_coin}{Colors.RESET} with rate {rate_color}{rate:.4f}%{Colors.RESET}")
    
    async def check_hourly_funding_rates(self):
        """
        Check funding rates at 50 minutes past each hour
        Switch positions if better opportunities exist
        """
        try:
            now = time.localtime()
            
            # Only run at 50 minutes past the hour
            if now.tm_min != 50:
                return
            
            logger.info(f"\n{Colors.BOLD}Running scheduled funding rate check (HH:50){Colors.RESET}")
            
            # Update funding rates
            await self.update_funding_rates()
            
            # Refresh positions
            self.refresh_positions()
            
            # Display position info
            self.display_position_info()
            
            # Find current active delta neutral position
            current_position_coin = None
            for coin_name in self.tracked_coins:
                if coin_name == "USDC":
                    continue
                
                is_delta_neutral, perp_size, spot_size, _ = self.positions.has_delta_neutral_position(coin_name)
                if is_delta_neutral:
                    current_position_coin = coin_name
                    logger.info(f"{Colors.GREEN}Active delta-neutral position: {Colors.YELLOW}{coin_name}{Colors.RESET}")
                    break
            
            if not current_position_coin:
                logger.info(f"{Colors.YELLOW}No active delta-neutral position found{Colors.RESET}")
                # Find best coin and create position if rate >= 5%
                best_coin = self.get_best_funding_rate_coin()
                if best_coin and self.coins[best_coin].perp.yearly_funding_rate >= 5.0:
                    logger.info(f"{Colors.GREEN}Creating new delta-neutral position for {Colors.YELLOW}{best_coin}{Colors.RESET}")
                    await self.positions.create_delta_position(best_coin)
                return
            
            # Check if current position yield < 5%
            current_yield = self.coins[current_position_coin].perp.yearly_funding_rate
            logger.info(f"Current position yield: {current_yield:.4f}%")
            
            if current_yield is None or current_yield < 5.0:
                logger.info(f"{Colors.YELLOW}Current yield below 5%, looking for better options{Colors.RESET}")
                
                best_coin = self.get_best_funding_rate_coin()
                
                if not best_coin or self.coins[best_coin].perp.yearly_funding_rate < 5.0:
                    logger.info(f"{Colors.YELLOW}No coin with funding rate >= 5% found{Colors.RESET}")
                    return
                
                if best_coin == current_position_coin:
                    return
                
                best_rate = self.coins[best_coin].perp.yearly_funding_rate
                logger.info(f"{Colors.GREEN}Found better coin: {Colors.YELLOW}{best_coin}{Colors.GREEN} with yield: {best_rate:.4f}%{Colors.RESET}")
                
                # Close current and open new
                logger.info(f"{Colors.YELLOW}Closing position on {current_position_coin}{Colors.RESET}")
                close_result = self.positions.close_delta_position(current_position_coin)
                
                if close_result:
                    # Wait for closing orders
                    await asyncio.sleep(10)
                    await self.positions.check_pending_orders()
                    
                    logger.info(f"{Colors.GREEN}Creating new position for {best_coin}{Colors.RESET}")
                    await self.positions.create_delta_position(best_coin)
            else:
                logger.info(f"{Colors.GREEN}Current yield above 5%, no action needed{Colors.RESET}")
        
        except Exception as e:
            logger.error(f"{Colors.RED}Error in hourly funding rate check: {e}{Colors.RESET}", exc_info=True)
    
    async def start(self):
        """Start the bot's main execution loop"""
        if self._is_running:
            logger.info("Bot is already running")
            return
        
        self._is_running = True
        logger.info(f"{Colors.BOLD}Starting Delta bot...{Colors.RESET}")
        
        # Display account summary
        logger.info(f"\n{Colors.BOLD}Account Summary:{Colors.RESET}")
        logger.info(f"  Total Value: ${Colors.GREEN}{self.total_raw_usd:.2f}{Colors.RESET}")
        logger.info(f"  Account Value: ${Colors.GREEN}{self.account_value:.2f}{Colors.RESET}")
        logger.info(f"  Margin Used: ${Colors.YELLOW}{self.total_margin_used:.2f}{Colors.RESET}")
        
        # Update funding rates
        await self.update_funding_rates()
        
        # Display positions
        self.display_position_info()
        
        # Check allocation
        self.check_allocation()
        
        # Check for initial position creation
        best_coin = self.get_best_funding_rate_coin()
        if best_coin and self.coins[best_coin].perp.yearly_funding_rate >= 5.0:
            is_delta_neutral, _, _, _ = self.positions.has_delta_neutral_position(best_coin)
            if not is_delta_neutral:
                logger.info(f"{Colors.GREEN}Creating initial delta-neutral position for {Colors.YELLOW}{best_coin}{Colors.RESET}")
                await self.positions.create_delta_position(best_coin)
        
        # Main loop
        logger.info(f"\n{Colors.BOLD}Entering main monitoring loop{Colors.RESET}")
        while self._is_running:
            try:
                # Check pending orders
                await self.positions.check_pending_orders()
                
                # Check hourly funding rates (runs only at HH:50)
                await self.check_hourly_funding_rates()
                
                # Sleep for refresh interval
                await asyncio.sleep(self.config.refresh_interval_sec)
                
            except KeyboardInterrupt:
                logger.info(f"{Colors.YELLOW}Keyboard interrupt detected{Colors.RESET}")
                break
            except Exception as e:
                logger.error(f"{Colors.RED}Error in main loop: {e}{Colors.RESET}", exc_info=True)
                await asyncio.sleep(60)
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping Delta bot...")
        self._is_running = False
    
    async def close_all_positions(self) -> bool:
        """Close all active delta-neutral positions"""
        logger.info("Closing all delta-neutral positions...")
        
        closed_count = 0
        for coin_name in self.tracked_coins:
            if coin_name == "USDC":
                continue
            
            is_delta_neutral, _, _, _ = self.positions.has_delta_neutral_position(coin_name)
            if is_delta_neutral:
                logger.info(f"Closing position for {coin_name}...")
                if self.positions.close_delta_position(coin_name):
                    closed_count += 1
        
        if closed_count > 0:
            logger.info(f"Successfully closed {closed_count} positions")
            return True
        else:
            logger.info("No positions were closed")
            return False
    
    async def exit_program(self, close_positions: bool = True):
        """Exit the program and optionally close all positions"""
        logger.info("Exiting program...")
        self._is_running = False
        
        if close_positions:
            await self.close_all_positions()
        
        logger.info("Exited")
        return True
