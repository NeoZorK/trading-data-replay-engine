"""
Historical data replay engine with latency-aware timing.
"""
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, List, Optional

from ..models import TradingMessage
from ..csv_parser import CSVParser
from .base import BaseReplayEngine
from ..logger import get_logger

logger = get_logger(__name__)


class HistoricalReplayEngine(BaseReplayEngine):
    """
    Historical data replay engine that respects timestamp + latency ordering.
    """
    
    def __init__(self, data_file: str, resume_from_index: Optional[int] = None):
        """
        Initialize historical replay engine.
        
        Args:
            data_file: Path to historical data CSV file
            resume_from_index: Index to resume from (for state persistence)
        """
        super().__init__(mode="historical")
        self.data_file = data_file
        self.messages: List[TradingMessage] = []
        self.resume_from_index = resume_from_index
        self.current_index = resume_from_index or 0
        self.last_effective_time: Optional[datetime] = None
        
    async def start(self) -> None:
        """Start the historical replay engine."""
        try:
            logger.info("Starting historical replay engine", 
                       file=self.data_file,
                       resume_from=self.resume_from_index)
            
            # Load and parse historical data
            self.messages = CSVParser.parse_historical_data(self.data_file)
            
            if self.resume_from_index:
                self.current_index = self.resume_from_index
                logger.info("Resuming from index", index=self.current_index)
            
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("Historical replay engine started", 
                       total_messages=len(self.messages),
                       current_index=self.current_index)
                       
        except Exception as e:
            logger.error("Failed to start historical replay engine", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the historical replay engine."""
        self.is_running = False
        logger.info("Historical replay engine stopped", 
                   current_index=self.current_index)
    
    async def replay_messages(self) -> AsyncGenerator[TradingMessage, None]:
        """
        Replay historical messages in chronological order.
        Respects effective arrival time (timestamp + latency).
        """
        if not self.messages:
            logger.warning("No messages loaded for replay")
            return
        
        logger.info("Starting message replay", 
                   total_messages=len(self.messages),
                   start_index=self.current_index)
        
        while self.is_running and self.current_index < len(self.messages):
            message = self.messages[self.current_index]
            
            # Calculate effective arrival time
            effective_time = self._calculate_effective_time(message)
            
            # Wait for the correct time if this is not the first message
            if self.last_effective_time is not None:
                wait_time = (effective_time - self.last_effective_time).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            # Update tracking
            self.last_effective_time = effective_time
            self.current_index += 1
            
            logger.debug("Replaying message", 
                        index=message.index,
                        ticker=message.ticker,
                        effective_time=effective_time.isoformat())
            
            yield message
        
        logger.info("Historical replay completed", 
                   total_processed=self.current_index)
    
    def _calculate_effective_time(self, message: TradingMessage) -> datetime:
        """
        Calculate effective arrival time (timestamp + latency).
        
        Args:
            message: Trading message
            
        Returns:
            Effective arrival time
        """
        latency_ms = message.latency or 0
        latency_delta = timedelta(milliseconds=latency_ms)
        return message.timestamp + latency_delta
    
    async def switch_mode(self, new_mode: str) -> None:
        """
        Switch to a different replay mode.
        
        Args:
            new_mode: New replay mode
        """
        if new_mode == "live":
            logger.info("Switching to live mode", 
                       current_index=self.current_index)
            # Save current state for potential resume
            self.resume_from_index = self.current_index
        else:
            logger.warning("Unknown mode", mode=new_mode)
    
    def get_resume_index(self) -> int:
        """
        Get the current index for state persistence.
        
        Returns:
            Current message index
        """
        return self.current_index
    
    def get_progress(self) -> dict:
        """
        Get replay progress information.
        
        Returns:
            Dictionary with progress information
        """
        total = len(self.messages)
        progress_pct = (self.current_index / total * 100) if total > 0 else 0
        
        return {
            **self.get_status(),
            "total_messages": total,
            "current_index": self.current_index,
            "progress_percentage": round(progress_pct, 2),
            "last_effective_time": self.last_effective_time.isoformat() if self.last_effective_time else None
        }
