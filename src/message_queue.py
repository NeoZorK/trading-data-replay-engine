"""
High-performance message queue implementation using Redis.
Supports thousands of messages per second with backpressure handling.
"""
import asyncio
import json
import redis.asyncio as redis
from typing import AsyncGenerator, Optional, Any
from datetime import datetime, timedelta

from .models import TradingMessage
from .logger import get_logger

logger = get_logger(__name__)


class MessageQueue:
    """
    High-performance message queue using Redis Streams.
    Supports multiple consumers and backpressure handling.
    """
    
    def __init__(
        self, 
        redis_url: str = "redis://localhost:6379",
        stream_name: str = "trading_messages",
        max_len: int = 10000,
        consumer_group: str = "mid_price_processor"
    ):
        """
        Initialize the message queue.
        
        Args:
            redis_url: Redis connection URL
            stream_name: Name of the Redis stream
            max_len: Maximum length of the stream (for backpressure)
            consumer_group: Consumer group name for multiple consumers
        """
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.max_len = max_len
        self.consumer_group = consumer_group
        self.redis_client: Optional[redis.Redis] = None
        self.consumer_name = f"consumer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Create consumer group if it doesn't exist
            try:
                await self.redis_client.xgroup_create(
                    self.stream_name, 
                    self.consumer_group, 
                    id="0", 
                    mkstream=True
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
                    
            logger.info("Connected to Redis message queue", 
                       stream=self.stream_name, 
                       consumer_group=self.consumer_group)
                       
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def publish(self, message: TradingMessage) -> None:
        """
        Publish a trading message to the queue.
        
        Args:
            message: Trading message to publish
        """
        if not self.redis_client:
            raise RuntimeError("Queue not connected")
        
        try:
            # Convert message to dict for Redis
            message_data = message.dict()
            message_data["timestamp"] = message.timestamp.isoformat()
            
            # Add to stream with max length for backpressure
            await self.redis_client.xadd(
                self.stream_name,
                message_data,
                maxlen=self.max_len,
                approximate=True
            )
            
            logger.debug("Published message", 
                        ticker=message.ticker, 
                        timestamp=message.timestamp)
                        
        except Exception as e:
            logger.error("Failed to publish message", 
                        error=str(e), 
                        ticker=message.ticker)
            raise
    
    async def consume(self, count: int = 10, block: int = 1000) -> AsyncGenerator[TradingMessage, None]:
        """
        Consume messages from the queue.
        
        Args:
            count: Number of messages to read at once
            block: Block time in milliseconds
            
        Yields:
            TradingMessage objects
        """
        if not self.redis_client:
            raise RuntimeError("Queue not connected")
        
        try:
            while True:
                # Read from stream
                messages = await self.redis_client.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.stream_name: ">"},
                    count=count,
                    block=block
                )
                
                if not messages:
                    continue
                
                for stream, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        try:
                            # Parse message
                            message_data = dict(fields)
                            message_data["timestamp"] = datetime.fromisoformat(
                                message_data["timestamp"]
                            )
                            if message_data.get("latency"):
                                message_data["latency"] = float(message_data["latency"])
                            
                            message = TradingMessage(**message_data)
                            
                            # Acknowledge message
                            await self.redis_client.xack(
                                self.stream_name,
                                self.consumer_group,
                                message_id
                            )
                            
                            yield message
                            
                        except Exception as e:
                            logger.error("Failed to parse message", 
                                       error=str(e), 
                                       message_id=message_id)
                            
                            # Acknowledge failed message to avoid reprocessing
                            await self.redis_client.xack(
                                self.stream_name,
                                self.consumer_group,
                                message_id
                            )
                            
        except Exception as e:
            logger.error("Error consuming messages", error=str(e))
            raise
    
    async def get_queue_length(self) -> int:
        """Get current queue length."""
        if not self.redis_client:
            return 0
        
        try:
            info = await self.redis_client.xinfo_stream(self.stream_name)
            return info.get("length", 0)
        except Exception as e:
            logger.error("Failed to get queue length", error=str(e))
            return 0
    
    async def clear_queue(self) -> None:
        """Clear all messages from the queue."""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(self.stream_name)
            logger.info("Cleared message queue")
        except Exception as e:
            logger.error("Failed to clear queue", error=str(e))
            raise
