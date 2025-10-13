"""
Live data replay engine with websocket simulation.
"""
import asyncio
import json
import websockets
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any

from ..models import TradingMessage
from ..csv_parser import CSVParser
from .base import BaseReplayEngine
from ..logger import get_logger

logger = get_logger(__name__)


class LiveReplayEngine(BaseReplayEngine):
    """
    Live data replay engine that simulates websocket data stream.
    """
    
    def __init__(self, data_file: str, websocket_url: str = "ws://localhost:8765"):
        """
        Initialize live replay engine.
        
        Args:
            data_file: Path to live data CSV file
            websocket_url: WebSocket URL for live data simulation
        """
        super().__init__(mode="live")
        self.data_file = data_file
        self.websocket_url = websocket_url
        self.messages: list[TradingMessage] = []
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.current_index = 0
        
    async def start(self) -> None:
        """Start the live replay engine."""
        try:
            logger.info("Starting live replay engine", 
                       file=self.data_file,
                       websocket_url=self.websocket_url)
            
            # Load live data for simulation
            self.messages = CSVParser.parse_live_data(self.data_file)
            
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("Live replay engine started", 
                       total_messages=len(self.messages))
                       
        except Exception as e:
            logger.error("Failed to start live replay engine", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the live replay engine."""
        self.is_running = False
        if self.websocket:
            await self.websocket.close()
        logger.info("Live replay engine stopped")
    
    async def replay_messages(self) -> AsyncGenerator[TradingMessage, None]:
        """
        Replay live messages as they would arrive via websocket.
        """
        if not self.messages:
            logger.warning("No messages loaded for live replay")
            return
        
        logger.info("Starting live message replay", 
                   total_messages=len(self.messages))
        
        # Simulate real-time data arrival
        for message in self.messages:
            if not self.is_running:
                break
            
            # Simulate network delay (random 1-50ms)
            await asyncio.sleep(0.001)  # 1ms base delay
            
            logger.debug("Replaying live message", 
                        index=message.index,
                        ticker=message.ticker,
                        timestamp=message.timestamp.isoformat())
            
            yield message
        
        logger.info("Live replay completed", 
                   total_processed=len(self.messages))
    
    async def switch_mode(self, new_mode: str) -> None:
        """
        Switch to a different replay mode.
        
        Args:
            new_mode: New replay mode
        """
        if new_mode == "historical":
            logger.info("Switching to historical mode")
        else:
            logger.warning("Unknown mode", mode=new_mode)
    
    async def start_websocket_server(self, port: int = 8765) -> None:
        """
        Start a websocket server to simulate live data feed.
        
        Args:
            port: Port to run the websocket server on
        """
        async def handle_client(websocket, path):
            """Handle websocket client connections."""
            logger.info("New websocket client connected", 
                       client=websocket.remote_address)
            
            try:
                # Send live data messages
                async for message in self.replay_messages():
                    if not self.is_running:
                        break
                    
                    # Convert message to JSON
                    message_data = message.dict()
                    message_data["timestamp"] = message.timestamp.isoformat()
                    
                    await websocket.send(json.dumps(message_data))
                    
                    # Small delay to simulate real-time
                    await asyncio.sleep(0.01)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.info("Websocket client disconnected")
            except Exception as e:
                logger.error("Error in websocket handler", error=str(e))
        
        # Start websocket server
        start_server = websockets.serve(handle_client, "localhost", port)
        await start_server
        logger.info("Websocket server started", port=port)
    
    async def connect_to_websocket(self, url: str) -> AsyncGenerator[TradingMessage, None]:
        """
        Connect to a websocket and receive live data.
        
        Args:
            url: WebSocket URL
            
        Yields:
            TradingMessage objects received from websocket
        """
        try:
            async with websockets.connect(url) as websocket:
                logger.info("Connected to websocket", url=url)
                
                async for message_json in websocket:
                    if not self.is_running:
                        break
                    
                    try:
                        # Parse JSON message
                        data = json.loads(message_json)
                        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                        
                        message = TradingMessage(**data)
                        
                        logger.debug("Received live message", 
                                   ticker=message.ticker,
                                   timestamp=message.timestamp.isoformat())
                        
                        yield message
                        
                    except Exception as e:
                        logger.error("Failed to parse websocket message", 
                                   error=str(e),
                                   message=message_json)
                        continue
                        
        except Exception as e:
            logger.error("Websocket connection error", error=str(e))
            raise
    
    def get_progress(self) -> dict:
        """
        Get live replay progress information.
        
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
            "websocket_url": self.websocket_url
        }
