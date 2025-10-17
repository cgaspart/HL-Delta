# Quick Start Guide - HL-Delta V2

Get up and running with HL-Delta V2 in minutes.

## Prerequisites

- Python 3.8 or higher
- Hyperliquid account with API access
- Basic understanding of delta-neutral trading

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/cgaspart/HL-Delta.git
cd HL-Delta
```

### Step 2: Install Dependencies

```bash
# Option A: Install in development mode (recommended)
pip install -e ".[dev]"

# Option B: Install production only
pip install -e .
```

## Configuration

### Step 1: Set Environment Variables

Create a `.env` file in the project root:

```bash
cat > .env << EOF
HYPERLIQUID_PRIVATE_KEY=your_private_key_here
HYPERLIQUID_ADDRESS=your_eth_address_here
API_SECRET_KEY=your_secret_key_here
EOF
```

**Important**: Replace the placeholder values with your actual credentials.

### Step 2: Configure Trading Parameters (Optional)

The `config.json` file has sensible defaults, but you can customize:

```json
{
  "general": {
    "debug": false,
    "tracked_coins": ["BTC", "ETH", "HYPE", "USDC"],
    "autostart": true
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
```

## Running the Bot

### Test Your Configuration

```bash
python example.py
```

This will:
- Load your configuration
- Connect to Hyperliquid
- Display your current positions
- Show funding rates
- Exit without trading

### Start the Bot

```bash
python entrypoint.py
```

The bot will:
1. Initialize and connect to Hyperliquid
2. Load your positions
3. Fetch current funding rates
4. Create delta-neutral positions if profitable (≥5% APR)
5. Monitor and switch positions as needed

### Using the API

Start the bot with API enabled (default):

```bash
python entrypoint.py
```

Access the API at `http://localhost:8080`

**Example API calls:**

```bash
# Get bot status
curl http://localhost:8080/api/status \
  -H "X-API-Key: your_secret_key_here"

# Start the bot
curl -X POST http://localhost:8080/api/bot/start \
  -H "X-API-Key: your_secret_key_here"

# Stop the bot
curl -X POST http://localhost:8080/api/bot/stop \
  -H "X-API-Key: your_secret_key_here"
```

## Using the Frontend

### Step 1: Start the Backend

```bash
python entrypoint.py
```

### Step 2: Configure Frontend

Create `frontend/.env`:

```bash
echo "REACT_APP_API_KEY=your_secret_key_here" > frontend/.env
```

### Step 3: Start Frontend

```bash
cd frontend
npm install
npm start
```

Access the UI at `http://localhost:3000`

## Basic Usage Examples

### Example 1: Simple Bot Usage

```python
import asyncio
from delta_bot import DeltaBot

async def main():
    # Create bot instance
    bot = DeltaBot(config_path="config.json")
    
    # Display current positions
    bot.display_position_info()
    
    # Start trading
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Manual Position Management

```python
import asyncio
from delta_bot import DeltaBot

async def main():
    bot = DeltaBot()
    
    # Update funding rates
    await bot.update_funding_rates()
    
    # Find best coin
    best_coin = bot.get_best_funding_rate_coin()
    print(f"Best coin: {best_coin}")
    
    # Create position manually
    if best_coin:
        await bot.positions.create_delta_position(best_coin)
    
    # Wait for orders to fill
    await asyncio.sleep(60)
    await bot.positions.check_pending_orders()
    
    # Close position
    bot.positions.close_delta_position(best_coin)

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Configuration Access

```python
from delta_bot import DeltaBot

bot = DeltaBot()

# Access configuration
print(f"Tracked coins: {bot.config.tracked_coins}")
print(f"Spot allocation: {bot.config.spot_allocation_pct * 100}%")
print(f"Refresh interval: {bot.config.refresh_interval_sec}s")

# Check allocation
allocation_ok = bot.check_allocation()
if not allocation_ok:
    print("Portfolio needs rebalancing")
```

## Docker Deployment

### Build Image

```bash
./build.sh
```

### Run Container

```bash
docker run -d \
  --name delta-bot \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/config.json:/app/config.json \
  hypervault-tradingbot:delta-2.0.0
```

### View Logs

```bash
docker logs -f delta-bot
```

### Stop Container

```bash
docker stop delta-bot
docker rm delta-bot
```

## Monitoring

### Check Logs

```bash
# View real-time logs
tail -f delta.log

# Search for errors
grep ERROR delta.log

# View last 100 lines
tail -n 100 delta.log
```

### Monitor Positions

The bot logs position information every hour at HH:50:

```
2024-10-18 10:50:00 - Running scheduled funding rate check (HH:50)
2024-10-18 10:50:01 - Active delta-neutral position: BTC
2024-10-18 10:50:01 - Current position yield: 8.5432%
```

## Troubleshooting

### Issue: Import Error

```bash
# Solution: Install the package
pip install -e .
```

### Issue: Configuration Not Found

```bash
# Solution: Ensure config.json exists
ls -la config.json

# Or specify path explicitly
python entrypoint.py --config /path/to/config.json
```

### Issue: API Connection Failed

```bash
# Solution: Check environment variables
python -c "import os; print(os.getenv('HYPERLIQUID_PRIVATE_KEY'))"

# Reload environment
source .env
```

### Issue: Orders Not Filling

- Check you have sufficient USDC balance
- Verify market liquidity
- Review order prices in logs
- Wait for order timeout (5 minutes)

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=delta_bot

# Run specific test
pytest tests/test_config.py -v
```

### Test Configuration

```bash
# Validate config.json
python -m json.tool config.json
```

### Test Connection

```bash
# Run example script
python example.py
```

## Next Steps

1. **Read the full documentation**: [README_V2.md](README_V2.md)
2. **Understand the strategy**: Review delta-neutral trading concepts
3. **Start small**: Test with minimal capital first
4. **Monitor closely**: Watch the first few hours of operation
5. **Adjust parameters**: Tune configuration based on performance

## Common Commands

```bash
# Install package
pip install -e .

# Run bot
python entrypoint.py

# Run example
python example.py

# Run tests
pytest

# Format code
black src/

# Check types
mypy src/

# Build Docker image
./build.sh

# View logs
tail -f delta.log
```

## Safety Tips

1. **Start with small amounts** to test the bot
2. **Monitor the first 24 hours** closely
3. **Set up alerts** for unusual activity
4. **Keep API keys secure** - never commit to git
5. **Understand the risks** of automated trading
6. **Have an exit plan** - know how to stop the bot quickly

## Getting Help

- **Documentation**: [README_V2.md](README_V2.md)
- **Migration Guide**: [MIGRATION_V2.md](MIGRATION_V2.md)
- **Issues**: [GitHub Issues](https://github.com/cgaspart/HL-Delta/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cgaspart/HL-Delta/discussions)

## Resources

- [Hyperliquid Documentation](https://hyperliquid.gitbook.io/)
- [Delta-Neutral Strategy Guide](https://www.investopedia.com/terms/d/deltaneutral.asp)
- [Python Async Programming](https://docs.python.org/3/library/asyncio.html)

---

**Ready to trade? Start with `python example.py` to verify your setup!**
