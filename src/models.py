"""
Data models for trading messages and replay engine.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class TradingMessage(BaseModel):
    """Trading message model for both historical and live data."""
    
    index: int
    timestamp: datetime
    ticker: str
    ask_amount: float
    ask_price: float
    bid_price: float
    bid_amount: float
    latency: Optional[float] = None  # Only present in historical data
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReplayMode(BaseModel):
    """Replay mode configuration."""
    
    mode: Literal["historical", "live"] = "historical"
    latency_threshold: float = 20.0  # ms
    resume_from_index: Optional[int] = None


class MidPriceResult(BaseModel):
    """Mid-price calculation result."""
    
    timestamp: datetime
    mid_price: float
    ticker: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorLog(BaseModel):
    """Error log entry."""
    
    timestamp: datetime
    message: str
    ticker: Optional[str] = None
    latency: Optional[float] = None
    threshold: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
