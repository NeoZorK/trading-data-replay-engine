"""
Unit tests for CSV parser.
"""
import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile
import os

from src.csv_parser import CSVParser
from src.models import TradingMessage


class TestCSVParser:
    """Test CSVParser class."""
    
    def create_test_historical_csv(self) -> str:
        """Create a test historical CSV file."""
        data = {
            'index': [1, 2, 3],
            'timestamp': [
                '2025-01-01 12:00:00',
                '2025-01-01 12:00:01',
                '2025-01-01 12:00:02'
            ],
            'ticker': ['BTC-USD@BINANCE', 'ETH-USD@BINANCE', 'BTC-USD@BINANCE'],
            'ask_amount': [100.0, 200.0, 150.0],
            'ask_price': [50000.0, 3000.0, 50010.0],
            'bid_price': [49900.0, 2990.0, 50000.0],
            'bid_amount': [200.0, 300.0, 250.0],
            'latency': [5.0, 10.0, 15.0]
        }
        
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            return f.name
    
    def create_test_live_csv(self) -> str:
        """Create a test live CSV file."""
        data = {
            'index': [1, 2, 3],
            'timestamp': [
                '2025-01-01 12:00:00',
                '2025-01-01 12:00:01',
                '2025-01-01 12:00:02'
            ],
            'ticker': ['BTC-USD@BINANCE', 'ETH-USD@BINANCE', 'BTC-USD@BINANCE'],
            'ask_amount': [100.0, 200.0, 150.0],
            'ask_price': [50000.0, 3000.0, 50010.0],
            'bid_price': [49900.0, 2990.0, 50000.0],
            'bid_amount': [200.0, 300.0, 250.0]
        }
        
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            return f.name
    
    def test_parse_historical_data(self):
        """Test parsing historical data."""
        csv_file = self.create_test_historical_csv()
        
        try:
            messages = CSVParser.parse_historical_data(csv_file)
            
            assert len(messages) == 3
            assert all(isinstance(msg, TradingMessage) for msg in messages)
            assert messages[0].ticker == "BTC-USD@BINANCE"
            assert messages[0].latency == 5.0
            assert messages[1].ticker == "ETH-USD@BINANCE"
            assert messages[1].latency == 10.0
            
            # Check sorting by effective time
            effective_times = [
                msg.timestamp.timestamp() + (msg.latency or 0) / 1000
                for msg in messages
            ]
            assert effective_times == sorted(effective_times)
            
        finally:
            os.unlink(csv_file)
    
    def test_parse_live_data(self):
        """Test parsing live data."""
        csv_file = self.create_test_live_csv()
        
        try:
            messages = CSVParser.parse_live_data(csv_file)
            
            assert len(messages) == 3
            assert all(isinstance(msg, TradingMessage) for msg in messages)
            assert messages[0].ticker == "BTC-USD@BINANCE"
            assert messages[0].latency is None
            assert messages[1].ticker == "ETH-USD@BINANCE"
            assert messages[1].latency is None
            
        finally:
            os.unlink(csv_file)
    
    def test_get_data_info(self):
        """Test getting data file information."""
        csv_file = self.create_test_historical_csv()
        
        try:
            info = CSVParser.get_data_info(csv_file)
            
            assert info["total_records"] == 3
            assert "latency" in info["columns"]
            assert info["has_latency"] is True
            assert info["unique_tickers"] == 2
            assert info["unique_exchanges"] == 1
            
        finally:
            os.unlink(csv_file)
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file."""
        with pytest.raises(Exception):
            CSVParser.parse_historical_data("nonexistent.csv")
    
    def test_parse_invalid_csv(self):
        """Test parsing invalid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("invalid,csv,data\n")
            f.write("1,2,3\n")
            csv_file = f.name
        
        try:
            # The parser should handle invalid data gracefully and return empty list
            messages = CSVParser.parse_historical_data(csv_file)
            assert len(messages) == 0  # Should return empty list for invalid data
        finally:
            os.unlink(csv_file)
