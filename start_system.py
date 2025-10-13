#!/usr/bin/env python3
"""
Complete system startup script for Trading Data Replay Engine.
"""
import asyncio
import signal
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.apps.replay_app import ReplayApp
from src.apps.mid_price_app import MidPriceApp
from src.logger import setup_logging, get_logger

logger = get_logger(__name__)


class SystemManager:
    """Manages the complete trading data replay system."""
    
    def __init__(self):
        self.replay_app = None
        self.mid_price_app = None
        self.is_running = False
    
    async def start_system(self):
        """Start the complete system."""
        try:
            setup_logging()
            logger.info("Starting complete trading data replay system")
            
            # Start replay engine
            logger.info("Starting Part 1: Replay Engine")
            self.replay_app = ReplayApp()
            await self.replay_app.start()
            
            # Wait a bit for replay engine to start
            await asyncio.sleep(2)
            
            # Start mid-price processor
            logger.info("Starting Part 2: Mid-Price Processor")
            self.mid_price_app = MidPriceApp()
            await self.mid_price_app.start()
            
            self.is_running = True
            logger.info("Complete system started successfully")
            
            # Run both applications concurrently
            replay_task = asyncio.create_task(self.replay_app.run_replay())
            mid_price_task = asyncio.create_task(self.mid_price_app.processor.process_messages())
            
            # Wait for both tasks
            await asyncio.gather(replay_task, mid_price_task)
            
        except Exception as e:
            logger.error("Failed to start system", error=str(e))
            raise
    
    async def stop_system(self):
        """Stop the complete system."""
        try:
            self.is_running = False
            logger.info("Stopping complete system")
            
            if self.replay_app:
                await self.replay_app.stop()
                logger.info("Replay engine stopped")
            
            if self.mid_price_app:
                await self.mid_price_app.stop()
                logger.info("Mid-price processor stopped")
            
            logger.info("Complete system stopped")
            
        except Exception as e:
            logger.error("Error stopping system", error=str(e))


async def main():
    """Main function."""
    system = SystemManager()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        logger.info("Received shutdown signal", signal=signal_name, signum=signum)
        asyncio.create_task(system.stop_system())
    
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination
    
    try:
        await system.start_system()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("System error", error=str(e))
        sys.exit(1)
    finally:
        await system.stop_system()


if __name__ == "__main__":
    print("🚀 Starting Trading Data Replay Engine System")
    print("=" * 60)
    print("📊 Part 1: Replay Engine (Historical & Live Data)")
    print("💰 Part 2: Mid-Price Processor (Latency Filtering)")
    print("🔄 Redis Message Queue (High Performance)")
    print("=" * 60)
    
    asyncio.run(main())
