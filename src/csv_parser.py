"""
CSV parser for historical and live trading data.
"""
import pandas as pd
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .models import TradingMessage
from .logger import get_logger

logger = get_logger(__name__)


class CSVParser:
    """Parser for trading data CSV files."""
    
    @staticmethod
    def parse_historical_data(file_path: str) -> List[TradingMessage]:
        """
        Parse historical data CSV file.
        
        Args:
            file_path: Path to the historical data CSV file
            
        Returns:
            List of TradingMessage objects sorted by effective arrival time
        """
        try:
            df = pd.read_csv(file_path)
            logger.info("Loaded historical data", 
                       file=file_path, 
                       records=len(df))
            
            messages = []
            for _, row in df.iterrows():
                try:
                    # Parse timestamp
                    timestamp = pd.to_datetime(row['timestamp'])
                    
                    # Create message
                    message = TradingMessage(
                        index=int(row['index']),
                        timestamp=timestamp,
                        ticker=str(row['ticker']),
                        ask_amount=float(row['ask_amount']),
                        ask_price=float(row['ask_price']),
                        bid_price=float(row['bid_price']),
                        bid_amount=float(row['bid_amount']),
                        latency=float(row['latency']) if pd.notna(row['latency']) else None
                    )
                    messages.append(message)
                    
                except Exception as e:
                    logger.warning("Failed to parse row", 
                                 error=str(e), 
                                 row_index=row.name)
                    continue
            
            # Sort by effective arrival time (timestamp + latency)
            messages.sort(key=lambda m: m.timestamp.timestamp() + (m.latency or 0) / 1000)
            
            logger.info("Parsed historical data", 
                       total_messages=len(messages),
                       sorted_by_effective_time=True)
            
            return messages
            
        except Exception as e:
            logger.error("Failed to parse historical data", 
                        file=file_path, 
                        error=str(e))
            raise
    
    @staticmethod
    def parse_live_data(file_path: str) -> List[TradingMessage]:
        """
        Parse live data CSV file.
        
        Args:
            file_path: Path to the live data CSV file
            
        Returns:
            List of TradingMessage objects
        """
        try:
            df = pd.read_csv(file_path)
            logger.info("Loaded live data", 
                       file=file_path, 
                       records=len(df))
            
            messages = []
            for _, row in df.iterrows():
                try:
                    # Parse timestamp
                    timestamp = pd.to_datetime(row['timestamp'])
                    
                    # Create message (no latency for live data)
                    message = TradingMessage(
                        index=int(row['index']),
                        timestamp=timestamp,
                        ticker=str(row['ticker']),
                        ask_amount=float(row['ask_amount']),
                        ask_price=float(row['ask_price']),
                        bid_price=float(row['bid_price']),
                        bid_amount=float(row['bid_amount']),
                        latency=None
                    )
                    messages.append(message)
                    
                except Exception as e:
                    logger.warning("Failed to parse row", 
                                 error=str(e), 
                                 row_index=row.name)
                    continue
            
            logger.info("Parsed live data", 
                       total_messages=len(messages))
            
            return messages
            
        except Exception as e:
            logger.error("Failed to parse live data", 
                        file=file_path, 
                        error=str(e))
            raise
    
    @staticmethod
    def get_data_info(file_path: str) -> dict:
        """
        Get information about the data file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Dictionary with file information
        """
        try:
            df = pd.read_csv(file_path)
            
            info = {
                "file_path": file_path,
                "total_records": len(df),
                "columns": list(df.columns),
                "has_latency": "latency" in df.columns,
                "date_range": {
                    "start": df['timestamp'].min(),
                    "end": df['timestamp'].max()
                },
                "unique_tickers": df['ticker'].nunique(),
                "unique_exchanges": df['ticker'].str.extract(r'@(\w+)')[0].nunique()
            }
            
            logger.info("Data file info", **info)
            return info
            
        except Exception as e:
            logger.error("Failed to get data info", 
                        file=file_path, 
                        error=str(e))
            raise
