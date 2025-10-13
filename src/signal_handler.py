"""
Signal handling utilities for graceful shutdown.
"""
import asyncio
import signal
import sys
from typing import Callable, Optional
from src.logger import get_logger

logger = get_logger(__name__)


class GracefulShutdown:
    """Handle graceful shutdown with signal management."""
    
    def __init__(self, shutdown_callback: Optional[Callable] = None):
        """
        Initialize graceful shutdown handler.
        
        Args:
            shutdown_callback: Optional callback function to call during shutdown
        """
        self.shutdown_callback = shutdown_callback
        self.shutdown_requested = False
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        # Handle SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Handle SIGTERM (termination)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Handle SIGQUIT (quit with core dump) - optional
        if hasattr(signal, 'SIGQUIT'):
            signal.signal(signal.SIGQUIT, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info("Received shutdown signal", signal=signal_name, signum=signum)
        
        self.shutdown_requested = True
        
        # Call shutdown callback if provided
        if self.shutdown_callback:
            try:
                if asyncio.iscoroutinefunction(self.shutdown_callback):
                    asyncio.create_task(self.shutdown_callback())
                else:
                    self.shutdown_callback()
            except Exception as e:
                logger.error("Error in shutdown callback", error=str(e))
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self.shutdown_requested
    
    def request_shutdown(self) -> None:
        """Manually request shutdown."""
        logger.info("Manual shutdown requested")
        self.shutdown_requested = True


class AsyncSignalHandler:
    """Async-compatible signal handler."""
    
    def __init__(self, shutdown_callback: Optional[Callable] = None):
        """
        Initialize async signal handler.
        
        Args:
            shutdown_callback: Async callback function to call during shutdown
        """
        self.shutdown_callback = shutdown_callback
        self.shutdown_requested = False
        self._loop = None
    
    def setup(self, loop: asyncio.AbstractEventLoop) -> None:
        """Setup signal handlers for the given event loop."""
        self._loop = loop
        
        # Add signal handlers to the event loop
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, self._signal_handler, sig)
    
    def _signal_handler(self, signum: int) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info("Received shutdown signal", signal=signal_name, signum=signum)
        
        self.shutdown_requested = True
        
        # Call shutdown callback if provided
        if self.shutdown_callback:
            try:
                asyncio.create_task(self.shutdown_callback())
            except Exception as e:
                logger.error("Error in shutdown callback", error=str(e))
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self.shutdown_requested


def handle_keyboard_interrupt(func: Callable) -> Callable:
    """
    Decorator to handle KeyboardInterrupt gracefully.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with KeyboardInterrupt handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            print("\n👋 Application stopped by user")
            sys.exit(130)  # Standard exit code for SIGINT
        except Exception as e:
            logger.error("Application error", error=str(e))
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    return wrapper


def handle_async_keyboard_interrupt(func: Callable) -> Callable:
    """
    Decorator to handle KeyboardInterrupt in async functions.
    
    Args:
        func: Async function to wrap
        
    Returns:
        Wrapped async function with KeyboardInterrupt handling
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            print("\n👋 Application stopped by user")
            sys.exit(130)  # Standard exit code for SIGINT
        except Exception as e:
            logger.error("Application error", error=str(e))
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    return wrapper
