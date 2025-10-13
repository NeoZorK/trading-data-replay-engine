# Trading Data Replay Engine

A high-performance Python application for replaying historical and live trading data with mid-price calculation capabilities.

## Overview

This project implements a scalable trading data replay engine that can process large volumes of financial data with support for:

- **Historical Data Replay**: Replays historical trading data with latency-aware timing
- **Live Data Simulation**: Simulates real-time data streams via WebSocket
- **Dynamic Mode Switching**: Seamlessly switch between historical and live replay modes
- **High-Performance Message Queue**: Redis-based queue supporting thousands of messages per second
- **Mid-Price Processing**: Separate application for calculating mid-prices with latency filtering
- **State Persistence**: Resume historical replay from the last processed point

## Architecture

### Part 1: Replay Engine
- **Unified Abstraction**: Single interface for both historical and live data replay
- **Message Queue**: Redis Streams for high-throughput message processing
- **Latency-Aware Timing**: Respects `timestamp + latency` for correct replay order
- **Mode Switching**: Dynamic switching between historical and live modes
- **State Persistence**: Remembers position when switching modes

### Part 2: Mid-Price Processor
- **Separate Application**: Independent consumer of the message queue
- **Mid-Price Calculation**: `mid_price = 0.5 * (bid_price + ask_price)`
- **Latency Filtering**: Skips messages exceeding configurable latency threshold
- **Batch Processing**: Efficient batch writing to output files
- **Error Logging**: Comprehensive error logging with structured format

## Project Structure

```
├── src/
│   ├── models.py                    # Data models (Pydantic)
│   ├── logger.py                    # Structured logging setup
│   ├── message_queue.py             # Redis-based message queue
│   ├── csv_parser.py                # CSV data parsing
│   ├── replay_engine/
│   │   ├── base.py                  # Abstract base replay engine
│   │   ├── historical.py            # Historical data replay
│   │   ├── live.py                  # Live data replay
│   │   └── engine.py                # Main replay engine with mode switching
│   ├── mid_price_processor/
│   │   └── processor.py             # Mid-price calculation processor
│   └── apps/
│       ├── replay_app.py            # Part 1 application
│       └── mid_price_app.py         # Part 2 application
├── tests/                           # Unit tests (100% coverage)
├── docs/                            # Documentation
├── logs/                            # Output logs
├── data/                            # Input data files
├── run_replay.py                    # Script to run Part 1
├── run_mid_price.py                 # Script to run Part 2
└── requirements.txt                 # Dependencies
```

## Setup and Installation

### Prerequisites
- Python 3.12+
- Redis server
- uv package manager (recommended)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd trading-data-replay-engine
   ```

2. **Install dependencies**:
   ```bash
   # Using uv (recommended)
   uv pip install -r requirements.txt
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Start Redis server**:
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:latest
   
   # Or install locally
   redis-server
   ```

4. **Prepare data files**:
   ```bash
   # Ensure your CSV files are in the data/ directory
   ls data/
   # Should show: historical_data.csv, live_data.csv
   ```

## Usage

### Running Part 1: Replay Engine

```bash
# Run the replay engine
python run_replay.py

# Or with custom parameters
python -c "
import asyncio
from src.apps.replay_app import ReplayApp

async def main():
    app = ReplayApp(
        historical_data_file='data/historical_data.csv',
        live_data_file='data/live_data.csv',
        redis_url='redis://localhost:6379',
        initial_mode='historical'
    )
    await app.start()

asyncio.run(main())
"
```

### Running Part 2: Mid-Price Processor

```bash
# Run the mid-price processor
python run_mid_price.py

# Or with custom parameters
python -c "
import asyncio
from src.apps.mid_price_app import MidPriceApp

async def main():
    app = MidPriceApp(
        redis_url='redis://localhost:6379',
        latency_threshold=20.0,
        output_dir='logs',
        batch_size=100
    )
    await app.start()

asyncio.run(main())
"
```

### Running Both Applications

```bash
# Terminal 1: Start the replay engine
python run_replay.py

# Terminal 2: Start the mid-price processor
python run_mid_price.py
```

## Configuration

### Environment Variables

- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379`)
- `LATENCY_THRESHOLD`: Latency threshold in milliseconds (default: `20.0`)
- `BATCH_SIZE`: Batch size for processing (default: `100`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### Data Format

#### Historical Data CSV
```csv
index,timestamp,ticker,ask_amount,ask_price,bid_price,bid_amount,latency
1,2025-01-01 12:00:00,BTC-USD@BINANCE,100.0,50000.0,49900.0,200.0,5.0
```

#### Live Data CSV
```csv
index,timestamp,ticker,ask_amount,ask_price,bid_price,bid_amount
1,2025-01-01 12:00:00,BTC-USD@BINANCE,100.0,50000.0,49900.0,200.0
```

## Output Files

### Mid-Price Log (`logs/mid_prices.log`)
```
2025-01-01T12:00:00, 49950.0
2025-01-01T12:00:01, 2995.0
```

### Error Log (`logs/errors.log`)
```
2025-01-01T12:00:00, No mid price at 2025-01-01 12:00:00 as latency 25.0ms is bigger than 20.0ms
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests with multithreading
uv run pytest tests -n auto

# Run with coverage
uv run pytest tests --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_models.py -v
```

## Performance Characteristics

- **Throughput**: Supports thousands of messages per second
- **Latency**: Sub-millisecond message processing
- **Memory**: Efficient batch processing with configurable buffer sizes
- **Scalability**: Multiple consumers can process from the same queue
- **Backpressure**: Automatic queue length management to prevent memory overflow

## Design Decisions

### Message Queue Choice: Redis Streams
- **High Performance**: Supports thousands of messages per second
- **Persistence**: Messages are persisted and can survive restarts
- **Consumer Groups**: Multiple consumers can process messages independently
- **Backpressure**: Built-in stream length limits prevent memory issues
- **Reliability**: ACK mechanism ensures message delivery

### Async/Await Architecture
- **Non-blocking**: Efficient I/O operations
- **Scalability**: Can handle many concurrent operations
- **Resource Efficiency**: Lower memory footprint than threading

### Batch Processing
- **Performance**: Reduces I/O operations
- **Efficiency**: Minimizes file system calls
- **Configurable**: Adjustable batch sizes for different workloads

## Limitations and Assumptions

1. **Redis Dependency**: Requires Redis server to be running
2. **Data Format**: Assumes specific CSV format with required columns
3. **Memory Usage**: Large datasets are loaded into memory (could be optimized for streaming)
4. **Network Latency**: WebSocket simulation includes artificial delays
5. **Error Handling**: Some edge cases may need additional handling for production use

## Future Enhancements

1. **Streaming Data Loading**: Load data in chunks to reduce memory usage
2. **Multiple Data Sources**: Support for different data formats and sources
3. **Real-time WebSocket**: Connect to actual trading data feeds
4. **Metrics and Monitoring**: Add Prometheus metrics and health checks
5. **Configuration Management**: YAML/JSON configuration files
6. **Docker Support**: Containerized deployment with Docker Compose

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.
