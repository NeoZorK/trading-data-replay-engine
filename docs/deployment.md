# Deployment Guide

## Quick Start

### 1. Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd trading-data-replay-engine

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
redis-server

# Terminal 1: Start replay engine
python run_replay.py

# Terminal 2: Start mid-price processor
python run_mid_price.py
```

## Production Deployment

### Environment Variables

```bash
export REDIS_URL="redis://your-redis-server:6379"
export LATENCY_THRESHOLD="20.0"
export BATCH_SIZE="100"
export LOG_LEVEL="INFO"
```

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB+ recommended
- **Storage**: 1GB+ for logs and data
- **Network**: Low latency connection to Redis

### Monitoring

Monitor the following metrics:
- Queue length in Redis
- Processing rate (messages/second)
- Error rate
- Memory usage
- CPU usage

### Scaling

To scale the system:
1. Run multiple mid-price processor instances
2. Use Redis Cluster for high availability
3. Consider partitioning data by ticker or exchange
4. Implement load balancing for multiple replay engines

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check Redis server is running
   - Verify connection URL
   - Check firewall settings

2. **High Memory Usage**
   - Reduce batch size
   - Increase buffer flush frequency
   - Monitor queue length

3. **Slow Processing**
   - Check Redis performance
   - Increase batch size
   - Use faster storage for logs

### Logs Location

- Application logs: `logs/`
- Mid-price results: `logs/mid_prices.log`
- Error logs: `logs/errors.log`
- Redis logs: Check Redis configuration
