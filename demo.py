#!/usr/bin/env python3
"""
Demo script to showcase the trading data replay engine functionality.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.csv_parser import CSVParser
from src.models import TradingMessage
from src.logger import setup_logging, get_logger

logger = get_logger(__name__)


async def demo_csv_parsing():
    """Demonstrate CSV parsing functionality."""
    print("🔍 Demo: CSV Data Parsing")
    print("=" * 50)
    
    # Parse historical data
    print("📊 Parsing historical data...")
    historical_messages = CSVParser.parse_historical_data("data/historical_data.csv")
    print(f"✅ Loaded {len(historical_messages)} historical messages")
    
    # Show first few messages
    print("\n📋 First 3 historical messages:")
    for i, msg in enumerate(historical_messages[:3]):
        print(f"  {i+1}. {msg.ticker} - Ask: {msg.ask_price}, Bid: {msg.bid_price}, Latency: {msg.latency}ms")
    
    # Parse live data
    print("\n📊 Parsing live data...")
    live_messages = CSVParser.parse_live_data("data/live_data.csv")
    print(f"✅ Loaded {len(live_messages)} live messages")
    
    # Show first few messages
    print("\n📋 First 3 live messages:")
    for i, msg in enumerate(live_messages[:3]):
        print(f"  {i+1}. {msg.ticker} - Ask: {msg.ask_price}, Bid: {msg.bid_price}")
    
    return historical_messages, live_messages


def demo_mid_price_calculation():
    """Demonstrate mid-price calculation."""
    print("\n💰 Demo: Mid-Price Calculation")
    print("=" * 50)
    
    # Sample trading messages
    sample_messages = [
        TradingMessage(
            index=1,
            timestamp="2025-01-01 12:00:00",
            ticker="BTC-USD@BINANCE",
            ask_amount=100.0,
            ask_price=50000.0,
            bid_price=49900.0,
            bid_amount=200.0,
            latency=5.0
        ),
        TradingMessage(
            index=2,
            timestamp="2025-01-01 12:00:01",
            ticker="ETH-USD@BINANCE",
            ask_amount=200.0,
            ask_price=3000.0,
            bid_price=2990.0,
            bid_amount=300.0,
            latency=15.0
        ),
        TradingMessage(
            index=3,
            timestamp="2025-01-01 12:00:02",
            ticker="BTC-USD@BINANCE",
            ask_amount=150.0,
            ask_price=50010.0,
            bid_price=50000.0,
            bid_amount=250.0,
            latency=25.0  # Exceeds threshold
        )
    ]
    
    latency_threshold = 20.0
    
    print(f"🎯 Latency threshold: {latency_threshold}ms")
    print("\n📊 Processing messages:")
    
    for msg in sample_messages:
        # Calculate mid price
        mid_price = 0.5 * (msg.bid_price + msg.ask_price)
        
        # Check latency threshold
        if msg.latency and msg.latency > latency_threshold:
            print(f"  ❌ {msg.ticker}: Latency {msg.latency}ms > {latency_threshold}ms - SKIPPED")
        else:
            print(f"  ✅ {msg.ticker}: Mid-price = {mid_price:.2f} (Ask: {msg.ask_price}, Bid: {msg.bid_price})")


def demo_data_statistics():
    """Show data statistics."""
    print("\n📈 Demo: Data Statistics")
    print("=" * 50)
    
    # Get historical data info
    historical_info = CSVParser.get_data_info("data/historical_data.csv")
    live_info = CSVParser.get_data_info("data/live_data.csv")
    
    print("📊 Historical Data:")
    print(f"  • Total records: {historical_info['total_records']:,}")
    print(f"  • Unique tickers: {historical_info['unique_tickers']:,}")
    print(f"  • Unique exchanges: {historical_info['unique_exchanges']}")
    print(f"  • Date range: {historical_info['date_range']['start']} to {historical_info['date_range']['end']}")
    print(f"  • Has latency data: {historical_info['has_latency']}")
    
    print("\n📊 Live Data:")
    print(f"  • Total records: {live_info['total_records']:,}")
    print(f"  • Unique tickers: {live_info['unique_tickers']:,}")
    print(f"  • Unique exchanges: {live_info['unique_exchanges']}")
    print(f"  • Date range: {live_info['date_range']['start']} to {live_info['date_range']['end']}")
    print(f"  • Has latency data: {live_info['has_latency']}")


async def main():
    """Main demo function."""
    print("🚀 Trading Data Replay Engine - Demo")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    try:
        # Demo 1: CSV Parsing
        historical_messages, live_messages = await demo_csv_parsing()
        
        # Demo 2: Mid-price calculation
        demo_mid_price_calculation()
        
        # Demo 3: Data statistics
        demo_data_statistics()
        
        print("\n🎉 Demo completed successfully!")
        print("\n📋 Next steps:")
        print("  1. Start Redis: brew services start redis")
        print("  2. Run Part 1: python3 run_replay.py")
        print("  3. Run Part 2: python3 run_mid_price.py")
        print("  4. Or use Docker: docker-compose up -d")
        
    except Exception as e:
        logger.error("Demo failed", error=str(e))
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        sys.exit(1)
