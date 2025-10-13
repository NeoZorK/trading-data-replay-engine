"""
Main application for the replay engine (Part 1).
"""
import asyncio
import signal
import sys
from pathlib import Path

from ..replay_engine.engine import ReplayEngine
from ..message_queue import MessageQueue
from ..logger import setup_logging, get_logger

logger = get_logger(__name__)


class ReplayApp:
    """
    Main application for the trading data replay engine.
    """
    
    def __init__(
        self,
        historical_data_file: str = "data/historical_data.csv",
        live_data_file: str = "data/live_data.csv",
        redis_url: str = "redis://localhost:6379",
        initial_mode: str = "historical"
    ):
        """
        Initialize the replay application.
        
        Args:
            historical_data_file: Path to historical data CSV
            live_data_file: Path to live data CSV
            redis_url: Redis connection URL
            initial_mode: Initial replay mode
        """
        self.historical_data_file = historical_data_file
        self.live_data_file = live_data_file
        self.redis_url = redis_url
        self.initial_mode = initial_mode
        
        # Initialize components
        self.message_queue = MessageQueue(redis_url=redis_url)
        self.replay_engine = ReplayEngine(
            historical_data_file=historical_data_file,
            live_data_file=live_data_file,
            message_queue=self.message_queue,
            initial_mode=initial_mode
        )
        
        self.is_running = False
    
    async def start(self) -> None:
        """Start the replay application."""
        try:
            # Setup logging
            setup_logging()
            
            logger.info("Starting replay application", 
                       historical_file=self.historical_data_file,
                       live_file=self.live_data_file,
                       initial_mode=self.initial_mode)
            
            # Start replay engine
            await self.replay_engine.start()
            
            self.is_running = True
            
            # Start replay task
            replay_task = asyncio.create_task(self.replay_engine.run_replay())
            
            # Start status monitoring task
            status_task = asyncio.create_task(self._monitor_status())
            
            # Start mode switching task
            mode_task = asyncio.create_task(self._handle_mode_switching())
            
            logger.info("Replay application started successfully")
            
            # Wait for tasks
            await asyncio.gather(replay_task, status_task, mode_task)
            
        except Exception as e:
            logger.error("Failed to start replay application", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the replay application."""
        try:
            self.is_running = False
            await self.replay_engine.stop()
            logger.info("Replay application stopped")
        except Exception as e:
            logger.error("Error stopping replay application", error=str(e))
    
    async def _monitor_status(self) -> None:
        """Monitor and log application status."""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Log status every 30 seconds
                
                status = self.replay_engine.get_status()
                queue_status = await self.replay_engine.get_queue_status()
                
                logger.info("Application status", 
                           status=status,
                           queue=queue_status)
                
            except Exception as e:
                logger.error("Error monitoring status", error=str(e))
                await asyncio.sleep(5)
    
    async def _handle_mode_switching(self) -> None:
        """Handle dynamic mode switching via console input."""
        while self.is_running:
            try:
                # In a real application, this could be an API endpoint
                # For demo purposes, we'll simulate mode switching
                await asyncio.sleep(60)  # Switch mode every minute for demo
                
                if self.replay_engine.current_mode == "historical":
                    await self.replay_engine.switch_mode("live")
                else:
                    await self.replay_engine.switch_mode("historical")
                
            except Exception as e:
                logger.error("Error handling mode switching", error=str(e))
                await asyncio.sleep(5)


async def main():
    """Main entry point for the replay application."""
    app = ReplayApp()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(app.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Application error", error=str(e))
        sys.exit(1)
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
