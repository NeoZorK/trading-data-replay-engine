#!/usr/bin/env python3
"""
Script to run the mid-price processor (Part 2).
"""
import asyncio
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.apps.mid_price_app import MidPriceApp
from src.logger import setup_logging, get_logger

logger = get_logger(__name__)


class SignalHandler:
    """Handle system signals for graceful shutdown."""
    
    def __init__(self, app: MidPriceApp):
        self.app = app
        self.shutdown_requested = False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info("Received shutdown signal", signal=signal_name, signum=signum)
        self.shutdown_requested = True
        
        # Create shutdown task
        asyncio.create_task(self._shutdown())
    
    async def _shutdown(self):
        """Perform graceful shutdown."""
        try:
            logger.info("Starting graceful shutdown...")
            await self.app.stop()
            logger.info("Graceful shutdown completed")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
        finally:
            # Exit the event loop
            asyncio.get_event_loop().stop()


async def main():
    """Main function with signal handling."""
    try:
        setup_logging()
        logger.info("Starting mid-price processor application")
        
        # Create application
        app = MidPriceApp()
        
        # Setup signal handlers
        signal_handler = SignalHandler(app)
        signal.signal(signal.SIGINT, signal_handler.signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler.signal_handler)  # Termination
        
        # Start application
        await app.start()
        
        # Run until shutdown requested
        while not signal_handler.shutdown_requested:
            await asyncio.sleep(0.1)
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Application error", error=str(e))
        sys.exit(1)
    finally:
        logger.info("Application exiting")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Mid-price processor stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
