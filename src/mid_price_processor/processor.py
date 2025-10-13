"""
Mid-price processor that consumes messages from the queue and calculates mid prices.
"""
import asyncio
import aiofiles
from datetime import datetime
from typing import Optional
from pathlib import Path

from ..models import TradingMessage, MidPriceResult, ErrorLog
from ..message_queue import MessageQueue
from ..logger import get_logger

logger = get_logger(__name__)


class MidPriceProcessor:
    """
    High-performance mid-price processor with latency filtering.
    """
    
    def __init__(
        self,
        message_queue: MessageQueue,
        latency_threshold: float = 20.0,
        output_dir: str = "logs",
        batch_size: int = 100
    ):
        """
        Initialize the mid-price processor.
        
        Args:
            message_queue: Message queue to consume from
            latency_threshold: Latency threshold in milliseconds
            output_dir: Directory for output files
            batch_size: Number of messages to process in batch
        """
        self.message_queue = message_queue
        self.latency_threshold = latency_threshold
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        
        # Output files
        self.mid_prices_file = self.output_dir / "mid_prices.log"
        self.errors_file = self.output_dir / "errors.log"
        
        # Processing state
        self.is_running = False
        self.processed_count = 0
        self.error_count = 0
        self.current_mode = "historical"  # Default mode
        
        # Batch buffers
        self.mid_price_buffer: list[MidPriceResult] = []
        self.error_buffer: list[ErrorLog] = []
        
    async def start(self) -> None:
        """Start the mid-price processor."""
        try:
            # Create output directory
            self.output_dir.mkdir(exist_ok=True)
            
            # Connect to message queue
            await self.message_queue.connect()
            
            self.is_running = True
            logger.info("Mid-price processor started", 
                       latency_threshold=self.latency_threshold,
                       output_dir=str(self.output_dir))
            
        except Exception as e:
            logger.error("Failed to start mid-price processor", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the mid-price processor."""
        try:
            self.is_running = False
            logger.info("Stopping mid-price processor...")
            
            # Flush remaining buffers
            await self._flush_buffers()
            
            # Disconnect from message queue
            await self.message_queue.disconnect()
            
            logger.info("Mid-price processor stopped successfully", 
                       processed_count=self.processed_count,
                       error_count=self.error_count)
            
        except Exception as e:
            logger.error("Error stopping mid-price processor", error=str(e))
            raise
    
    async def set_mode(self, mode: str) -> None:
        """
        Set the current replay mode.
        
        Args:
            mode: Replay mode ("historical" or "live")
        """
        self.current_mode = mode
        logger.info("Mid-price processor mode set", mode=mode)
    
    async def process_messages(self) -> None:
        """
        Main processing loop that consumes messages and calculates mid prices.
        """
        logger.info("Starting message processing", 
                   mode=self.current_mode,
                   latency_threshold=self.latency_threshold)
        
        try:
            async for message in self.message_queue.consume():
                if not self.is_running:
                    break
                
                await self._process_message(message)
                
                # Log progress periodically
                if self.processed_count % 1000 == 0:
                    logger.info("Processing progress", 
                               processed=self.processed_count,
                               errors=self.error_count)
            
            logger.info("Message processing completed", 
                       total_processed=self.processed_count,
                       total_errors=self.error_count)
            
        except Exception as e:
            logger.error("Error during message processing", error=str(e))
            raise
    
    async def _process_message(self, message: TradingMessage) -> None:
        """
        Process a single trading message.
        
        Args:
            message: Trading message to process
        """
        try:
            # Check latency threshold for historical mode
            if self.current_mode == "historical" and message.latency is not None:
                if message.latency > self.latency_threshold:
                    await self._log_latency_error(message)
                    return
            
            # Calculate mid price
            mid_price = 0.5 * (message.bid_price + message.ask_price)
            
            # Create result
            result = MidPriceResult(
                timestamp=message.timestamp,
                mid_price=mid_price,
                ticker=message.ticker
            )
            
            # Add to buffer
            self.mid_price_buffer.append(result)
            
            # Flush buffer if full
            if len(self.mid_price_buffer) >= self.batch_size:
                await self._flush_mid_price_buffer()
            
            self.processed_count += 1
            
            logger.debug("Processed message", 
                        ticker=message.ticker,
                        mid_price=mid_price,
                        timestamp=message.timestamp.isoformat())
            
        except Exception as e:
            logger.error("Error processing message", 
                        error=str(e),
                        ticker=message.ticker)
            self.error_count += 1
    
    async def _log_latency_error(self, message: TradingMessage) -> None:
        """
        Log a latency threshold error.
        
        Args:
            message: Trading message that exceeded latency threshold
        """
        error_log = ErrorLog(
            timestamp=message.timestamp,
            message=f"No mid price at {message.timestamp} as latency {message.latency}ms is bigger than {self.latency_threshold}ms",
            ticker=message.ticker,
            latency=message.latency,
            threshold=self.latency_threshold
        )
        
        self.error_buffer.append(error_log)
        
        # Flush error buffer if full
        if len(self.error_buffer) >= self.batch_size:
            await self._flush_error_buffer()
        
        self.error_count += 1
        
        logger.debug("Latency threshold exceeded", 
                    ticker=message.ticker,
                    latency=message.latency,
                    threshold=self.latency_threshold)
    
    async def _flush_mid_price_buffer(self) -> None:
        """Flush mid-price buffer to file."""
        if not self.mid_price_buffer:
            return
        
        try:
            async with aiofiles.open(self.mid_prices_file, "a") as f:
                for result in self.mid_price_buffer:
                    # Format: 2025-01-01 00:00:00.120, 200.5
                    timestamp_str = result.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    line = f"{timestamp_str}, {result.mid_price}\n"
                    await f.write(line)
            
            logger.debug("Flushed mid-price buffer", 
                        count=len(self.mid_price_buffer))
            
            self.mid_price_buffer.clear()
            
        except Exception as e:
            logger.error("Failed to flush mid-price buffer", error=str(e))
            raise
    
    async def _flush_error_buffer(self) -> None:
        """Flush error buffer to file."""
        if not self.error_buffer:
            return
        
        try:
            async with aiofiles.open(self.errors_file, "a") as f:
                for error in self.error_buffer:
                    # Format: 2025-01-01 00:00:00.120, No mid price at ...
                    timestamp_str = error.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    line = f"{timestamp_str}, {error.message}\n"
                    await f.write(line)
            
            logger.debug("Flushed error buffer", 
                        count=len(self.error_buffer))
            
            self.error_buffer.clear()
            
        except Exception as e:
            logger.error("Failed to flush error buffer", error=str(e))
            raise
    
    async def _flush_buffers(self) -> None:
        """Flush all remaining buffers."""
        await self._flush_mid_price_buffer()
        await self._flush_error_buffer()
    
    def get_status(self) -> dict:
        """
        Get processor status.
        
        Returns:
            Dictionary with processor status information
        """
        return {
            "is_running": self.is_running,
            "current_mode": self.current_mode,
            "latency_threshold": self.latency_threshold,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "buffer_sizes": {
                "mid_price_buffer": len(self.mid_price_buffer),
                "error_buffer": len(self.error_buffer)
            },
            "output_files": {
                "mid_prices": str(self.mid_prices_file),
                "errors": str(self.errors_file)
            }
        }
