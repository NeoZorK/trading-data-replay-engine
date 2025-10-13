"""
Unit tests for mid-price processor.
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.mid_price_processor.processor import MidPriceProcessor
from src.models import TradingMessage


class TestMidPriceProcessor:
    """Test MidPriceProcessor class."""
    
    @pytest.fixture
    def mock_message_queue(self):
        """Create a mock message queue."""
        queue = AsyncMock()
        queue.connect = AsyncMock()
        queue.disconnect = AsyncMock()
        queue.consume = AsyncMock()
        return queue
    
    @pytest.fixture
    def sample_messages(self):
        """Create sample trading messages."""
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        
        return [
            TradingMessage(
                index=1,
                timestamp=base_time,
                ticker="BTC-USD@BINANCE",
                ask_amount=100.0,
                ask_price=50000.0,
                bid_price=49900.0,
                bid_amount=200.0,
                latency=5.0
            ),
            TradingMessage(
                index=2,
                timestamp=base_time,
                ticker="ETH-USD@BINANCE",
                ask_amount=200.0,
                ask_price=3000.0,
                bid_price=2990.0,
                bid_amount=300.0,
                latency=25.0  # Exceeds threshold
            ),
            TradingMessage(
                index=3,
                timestamp=base_time,
                ticker="BTC-USD@BINANCE",
                ask_amount=150.0,
                ask_price=50010.0,
                bid_price=50000.0,
                bid_amount=250.0,
                latency=None  # Live data
            )
        ]
    
    @pytest.mark.asyncio
    async def test_processor_initialization(self, mock_message_queue):
        """Test processor initialization."""
        processor = MidPriceProcessor(
            message_queue=mock_message_queue,
            latency_threshold=20.0,
            output_dir="test_logs",
            batch_size=10
        )
        
        assert processor.latency_threshold == 20.0
        assert processor.batch_size == 10
        assert processor.current_mode == "historical"
        assert processor.processed_count == 0
        assert processor.error_count == 0
    
    @pytest.mark.asyncio
    async def test_start_stop(self, mock_message_queue):
        """Test starting and stopping the processor."""
        processor = MidPriceProcessor(mock_message_queue)
        
        await processor.start()
        assert processor.is_running is True
        mock_message_queue.connect.assert_called_once()
        
        await processor.stop()
        assert processor.is_running is False
        mock_message_queue.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_mode(self, mock_message_queue):
        """Test setting processor mode."""
        processor = MidPriceProcessor(mock_message_queue)
        
        await processor.set_mode("live")
        assert processor.current_mode == "live"
        
        await processor.set_mode("historical")
        assert processor.current_mode == "historical"
    
    @pytest.mark.asyncio
    async def test_process_message_historical_within_threshold(self, mock_message_queue, sample_messages):
        """Test processing message within latency threshold."""
        processor = MidPriceProcessor(mock_message_queue, latency_threshold=20.0)
        await processor.start()
        
        message = sample_messages[0]  # latency=5.0
        await processor._process_message(message)
        
        assert processor.processed_count == 1
        assert processor.error_count == 0
        assert len(processor.mid_price_buffer) == 1
        
        result = processor.mid_price_buffer[0]
        assert result.mid_price == 49950.0  # (50000 + 49900) / 2
        assert result.ticker == "BTC-USD@BINANCE"
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_process_message_historical_exceeds_threshold(self, mock_message_queue, sample_messages):
        """Test processing message that exceeds latency threshold."""
        processor = MidPriceProcessor(mock_message_queue, latency_threshold=20.0)
        await processor.start()
        
        message = sample_messages[1]  # latency=25.0
        await processor._process_message(message)
        
        assert processor.processed_count == 0
        assert processor.error_count == 1
        assert len(processor.error_buffer) == 1
        
        error = processor.error_buffer[0]
        assert "latency 25.0ms is bigger than 20.0ms" in error.message
        assert error.ticker == "ETH-USD@BINANCE"
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_process_message_live_mode(self, mock_message_queue, sample_messages):
        """Test processing message in live mode (no latency check)."""
        processor = MidPriceProcessor(mock_message_queue, latency_threshold=20.0)
        await processor.start()
        await processor.set_mode("live")
        
        message = sample_messages[1]  # latency=25.0, but should be processed in live mode
        await processor._process_message(message)
        
        assert processor.processed_count == 1
        assert processor.error_count == 0
        assert len(processor.mid_price_buffer) == 1
        
        result = processor.mid_price_buffer[0]
        assert result.mid_price == 2995.0  # (3000 + 2990) / 2
        
        await processor.stop()
    
    def test_mid_price_calculation(self):
        """Test mid-price calculation formula."""
        # Test the formula: mid_price = 0.5 * (bid_price + ask_price)
        ask_price = 50000.0
        bid_price = 49900.0
        expected_mid_price = 0.5 * (ask_price + bid_price)
        
        assert expected_mid_price == 49950.0
    
    @pytest.mark.asyncio
    async def test_buffer_flushing(self, mock_message_queue):
        """Test buffer flushing functionality."""
        processor = MidPriceProcessor(mock_message_queue, batch_size=2)
        await processor.start()
        
        # Add messages to fill buffer
        message1 = TradingMessage(
            index=1,
            timestamp=datetime.now(),
            ticker="BTC-USD@BINANCE",
            ask_amount=100.0,
            ask_price=50000.0,
            bid_price=49900.0,
            bid_amount=200.0,
            latency=5.0
        )
        
        message2 = TradingMessage(
            index=2,
            timestamp=datetime.now(),
            ticker="ETH-USD@BINANCE",
            ask_amount=200.0,
            ask_price=3000.0,
            bid_price=2990.0,
            bid_amount=300.0,
            latency=5.0
        )
        
        await processor._process_message(message1)
        assert len(processor.mid_price_buffer) == 1
        
        await processor._process_message(message2)
        assert len(processor.mid_price_buffer) == 0  # Should be flushed
        
        await processor.stop()
    
    def test_get_status(self, mock_message_queue):
        """Test getting processor status."""
        processor = MidPriceProcessor(mock_message_queue)
        
        status = processor.get_status()
        
        assert "is_running" in status
        assert "current_mode" in status
        assert "latency_threshold" in status
        assert "processed_count" in status
        assert "error_count" in status
        assert "buffer_sizes" in status
        assert "output_files" in status
