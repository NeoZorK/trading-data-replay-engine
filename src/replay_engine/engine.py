"""
Main replay engine with dynamic mode switching and state persistence.
"""
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime

from ..models import TradingMessage, ReplayMode
from ..message_queue import MessageQueue
from .base import BaseReplayEngine
from .historical import HistoricalReplayEngine
from .live import LiveReplayEngine
from ..logger import get_logger

logger = get_logger(__name__)


class ReplayEngine:
    """
    Main replay engine with unified interface and dynamic mode switching.
    """
    
    def __init__(
        self,
        historical_data_file: str,
        live_data_file: str,
        message_queue: MessageQueue,
        initial_mode: str = "historical"
    ):
        """
        Initialize the replay engine.
        
        Args:
            historical_data_file: Path to historical data CSV
            live_data_file: Path to live data CSV
            message_queue: Message queue for publishing messages
            initial_mode: Initial replay mode
        """
        self.historical_data_file = historical_data_file
        self.live_data_file = live_data_file
        self.message_queue = message_queue
        
        # Initialize engines
        self.historical_engine = HistoricalReplayEngine(historical_data_file)
        self.live_engine = LiveReplayEngine(live_data_file)
        
        # Current state
        self.current_mode = initial_mode
        self.current_engine: Optional[BaseReplayEngine] = None
        self.is_running = False
        self.state: Dict[str, Any] = {}
        
    async def start(self) -> None:
        """Start the replay engine."""
        try:
            logger.info("Starting replay engine", mode=self.current_mode)
            
            # Connect to message queue
            await self.message_queue.connect()
            
            # Start the appropriate engine
            await self._switch_to_mode(self.current_mode)
            
            self.is_running = True
            logger.info("Replay engine started successfully")
            
        except Exception as e:
            logger.error("Failed to start replay engine", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the replay engine."""
        try:
            self.is_running = False
            
            # Stop current engine
            if self.current_engine:
                await self.current_engine.stop()
            
            # Disconnect from message queue
            await self.message_queue.disconnect()
            
            logger.info("Replay engine stopped")
            
        except Exception as e:
            logger.error("Error stopping replay engine", error=str(e))
    
    async def switch_mode(self, new_mode: str) -> None:
        """
        Dynamically switch between historical and live replay modes.
        
        Args:
            new_mode: New replay mode ("historical" or "live")
        """
        if new_mode not in ["historical", "live"]:
            raise ValueError(f"Invalid mode: {new_mode}")
        
        if new_mode == self.current_mode:
            logger.info("Already in requested mode", mode=new_mode)
            return
        
        try:
            logger.info("Switching replay mode", 
                       from_mode=self.current_mode, 
                       to_mode=new_mode)
            
            # Save current state
            await self._save_state()
            
            # Stop current engine
            if self.current_engine:
                await self.current_engine.stop()
            
            # Switch to new mode
            await self._switch_to_mode(new_mode)
            
            logger.info("Mode switch completed", new_mode=new_mode)
            
        except Exception as e:
            logger.error("Failed to switch mode", 
                        error=str(e),
                        from_mode=self.current_mode,
                        to_mode=new_mode)
            raise
    
    async def _switch_to_mode(self, mode: str) -> None:
        """
        Switch to the specified mode.
        
        Args:
            mode: Target replay mode
        """
        if mode == "historical":
            # Resume from saved state if available
            resume_index = self.state.get("historical_resume_index")
            if resume_index:
                self.historical_engine.resume_from_index = resume_index
                logger.info("Resuming historical replay", resume_index=resume_index)
            
            self.current_engine = self.historical_engine
            await self.current_engine.start()
            
        elif mode == "live":
            self.current_engine = self.live_engine
            await self.current_engine.start()
        
        self.current_mode = mode
        logger.info("Switched to mode", mode=mode)
    
    async def _save_state(self) -> None:
        """Save current engine state for persistence."""
        if self.current_engine and hasattr(self.current_engine, 'get_resume_index'):
            resume_index = self.current_engine.get_resume_index()
            self.state[f"{self.current_mode}_resume_index"] = resume_index
            logger.debug("Saved state", 
                        mode=self.current_mode, 
                        resume_index=resume_index)
    
    async def run_replay(self) -> None:
        """
        Run the replay engine and publish messages to the queue.
        """
        if not self.current_engine:
            raise RuntimeError("No engine is currently active")
        
        logger.info("Starting message replay and publishing", 
                   mode=self.current_mode)
        
        try:
            async for message in self.current_engine.replay_messages():
                if not self.is_running:
                    break
                
                # Publish message to queue
                await self.message_queue.publish(message)
                
                # Log progress periodically
                if message.index % 1000 == 0:
                    logger.info("Replay progress", 
                               index=message.index,
                               ticker=message.ticker)
            
            logger.info("Replay completed", mode=self.current_mode)
            
        except Exception as e:
            logger.error("Error during replay", error=str(e))
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive engine status.
        
        Returns:
            Dictionary with engine status information
        """
        status = {
            "current_mode": self.current_mode,
            "is_running": self.is_running,
            "state": self.state.copy()
        }
        
        if self.current_engine:
            status["engine_status"] = self.current_engine.get_status()
            if hasattr(self.current_engine, 'get_progress'):
                status["progress"] = self.current_engine.get_progress()
        
        return status
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get message queue status.
        
        Returns:
            Dictionary with queue status information
        """
        try:
            queue_length = await self.message_queue.get_queue_length()
            return {
                "queue_length": queue_length,
                "connected": self.message_queue.redis_client is not None
            }
        except Exception as e:
            logger.error("Failed to get queue status", error=str(e))
            return {"error": str(e)}
