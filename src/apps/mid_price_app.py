"""
Main application for the mid-price processor (Part 2).
"""
import asyncio
import signal
import sys

from ..mid_price_processor.processor import MidPriceProcessor
from ..message_queue import MessageQueue
from ..logger import setup_logging, get_logger

logger = get_logger(__name__)


class MidPriceApp:
    """
    Main application for the mid-price processor.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        latency_threshold: float = 20.0,
        output_dir: str = "logs",
        batch_size: int = 100
    ):
        """
        Initialize the mid-price application.
        
        Args:
            redis_url: Redis connection URL
            latency_threshold: Latency threshold in milliseconds
            output_dir: Directory for output files
            batch_size: Number of messages to process in batch
        """
        self.redis_url = redis_url
        self.latency_threshold = latency_threshold
        self.output_dir = output_dir
        self.batch_size = batch_size
        
        # Initialize components
        self.message_queue = MessageQueue(redis_url=redis_url)
        self.processor = MidPriceProcessor(
            message_queue=self.message_queue,
            latency_threshold=latency_threshold,
            output_dir=output_dir,
            batch_size=batch_size
        )
        
        self.is_running = False
    
    async def start(self) -> None:
        """Start the mid-price application."""
        try:
            # Setup logging
            setup_logging()
            
            logger.info("Starting mid-price application", 
                       redis_url=self.redis_url,
                       latency_threshold=self.latency_threshold,
                       output_dir=self.output_dir,
                       batch_size=self.batch_size)
            
            # Start processor
            await self.processor.start()
            
            self.is_running = True
            
            # Start processing task
            processing_task = asyncio.create_task(self.processor.process_messages())
            
            # Start status monitoring task
            status_task = asyncio.create_task(self._monitor_status())
            
            logger.info("Mid-price application started successfully")
            
            # Wait for tasks with proper cancellation handling
            try:
                await asyncio.gather(processing_task, status_task, return_exceptions=True)
            except asyncio.CancelledError:
                logger.info("Tasks cancelled, stopping application")
                # Cancel all tasks
                for task in [processing_task, status_task]:
                    if not task.done():
                        task.cancel()
                # Wait for cancellation to complete
                await asyncio.gather(processing_task, status_task, return_exceptions=True)
            
        except Exception as e:
            logger.error("Failed to start mid-price application", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the mid-price application."""
        try:
            self.is_running = False
            logger.info("Stopping mid-price application...")
            await self.processor.stop()
            logger.info("Mid-price application stopped successfully")
        except Exception as e:
            logger.error("Error stopping mid-price application", error=str(e))
            raise
    
    async def set_mode(self, mode: str) -> None:
        """
        Set the processor mode.
        
        Args:
            mode: Processing mode ("historical" or "live")
        """
        await self.processor.set_mode(mode)
        logger.info("Processor mode set", mode=mode)
    
    async def _monitor_status(self) -> None:
        """Monitor and log processor status."""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Log status every 30 seconds
                
                status = self.processor.get_status()
                logger.info("Processor status", status=status)
                
            except Exception as e:
                logger.error("Error monitoring status", error=str(e))
                await asyncio.sleep(5)


async def main():
    """Main entry point for the mid-price application."""
    app = MidPriceApp()
    
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
