"""
Unit tests for data models.
"""
import pytest
from datetime import datetime
from src.models import TradingMessage, MidPriceResult, ErrorLog, ReplayMode


class TestTradingMessage:
    """Test TradingMessage model."""
    
    def test_trading_message_creation(self):
        """Test creating a trading message."""
        timestamp = datetime.now()
        message = TradingMessage(
            index=1,
            timestamp=timestamp,
            ticker="BTC-USD@BINANCE",
            ask_amount=100.0,
            ask_price=50000.0,
            bid_price=49900.0,
            bid_amount=200.0,
            latency=5.0
        )
        
        assert message.index == 1
        assert message.timestamp == timestamp
        assert message.ticker == "BTC-USD@BINANCE"
        assert message.ask_amount == 100.0
        assert message.ask_price == 50000.0
        assert message.bid_price == 49900.0
        assert message.bid_amount == 200.0
        assert message.latency == 5.0
    
    def test_trading_message_without_latency(self):
        """Test creating a trading message without latency."""
        timestamp = datetime.now()
        message = TradingMessage(
            index=1,
            timestamp=timestamp,
            ticker="BTC-USD@BINANCE",
            ask_amount=100.0,
            ask_price=50000.0,
            bid_price=49900.0,
            bid_amount=200.0
        )
        
        assert message.latency is None
    
    def test_trading_message_serialization(self):
        """Test trading message serialization."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        message = TradingMessage(
            index=1,
            timestamp=timestamp,
            ticker="BTC-USD@BINANCE",
            ask_amount=100.0,
            ask_price=50000.0,
            bid_price=49900.0,
            bid_amount=200.0,
            latency=5.0
        )
        
        data = message.dict()
        assert data["timestamp"] == timestamp  # Pydantic v2 returns datetime object
        assert data["index"] == 1
        assert data["ticker"] == "BTC-USD@BINANCE"


class TestMidPriceResult:
    """Test MidPriceResult model."""
    
    def test_mid_price_result_creation(self):
        """Test creating a mid-price result."""
        timestamp = datetime.now()
        result = MidPriceResult(
            timestamp=timestamp,
            mid_price=49950.0,
            ticker="BTC-USD@BINANCE"
        )
        
        assert result.timestamp == timestamp
        assert result.mid_price == 49950.0
        assert result.ticker == "BTC-USD@BINANCE"


class TestErrorLog:
    """Test ErrorLog model."""
    
    def test_error_log_creation(self):
        """Test creating an error log."""
        timestamp = datetime.now()
        error = ErrorLog(
            timestamp=timestamp,
            message="Test error message",
            ticker="BTC-USD@BINANCE",
            latency=25.0,
            threshold=20.0
        )
        
        assert error.timestamp == timestamp
        assert error.message == "Test error message"
        assert error.ticker == "BTC-USD@BINANCE"
        assert error.latency == 25.0
        assert error.threshold == 20.0


class TestReplayMode:
    """Test ReplayMode model."""
    
    def test_replay_mode_creation(self):
        """Test creating a replay mode."""
        mode = ReplayMode(
            mode="historical",
            latency_threshold=20.0,
            resume_from_index=100
        )
        
        assert mode.mode == "historical"
        assert mode.latency_threshold == 20.0
        assert mode.resume_from_index == 100
    
    def test_replay_mode_defaults(self):
        """Test replay mode defaults."""
        mode = ReplayMode()
        
        assert mode.mode == "historical"
        assert mode.latency_threshold == 20.0
        assert mode.resume_from_index is None
