"""
Base replay engine with unified abstraction for historical and live data.
"""
import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from datetime import datetime

from ..models import TradingMessage, ReplayMode
from ..logger import get_logger

logger = get_logger(__name__)


class BaseReplayEngine(ABC):
    """
    Abstract base class for replay engines.
    Provides unified interface for both historical and live data replay.
    """
    
    def __init__(self, mode: str = "historical"):
        """
        Initialize the replay engine.
        
        Args:
            mode: Replay mode ("historical" or "live")
        """
        self.mode = mode
        self.is_running = False
        self.current_index = 0
        self.start_time: Optional[datetime] = None
        
    @abstractmethod
    async def start(self) -> None:
        """Start the replay engine."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the replay engine."""
        pass
    
    @abstractmethod
    async def replay_messages(self) -> AsyncGenerator[TradingMessage, None]:
        """
        Replay messages in chronological order.
        
        Yields:
            TradingMessage objects in correct chronological order
        """
        pass
    
    @abstractmethod
    async def switch_mode(self, new_mode: str) -> None:
        """
        Switch between historical and live replay modes.
        
        Args:
            new_mode: New replay mode ("historical" or "live")
        """
        pass
    
    def get_status(self) -> dict:
        """
        Get current engine status.
        
        Returns:
            Dictionary with engine status information
        """
        return {
            "mode": self.mode,
            "is_running": self.is_running,
            "current_index": self.current_index,
            "start_time": self.start_time.isoformat() if self.start_time else None
        }
