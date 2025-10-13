# Signal Handling and Graceful Shutdown

## Overview

All Python applications in this project now support graceful shutdown with proper signal handling for:
- **Ctrl+C** (SIGINT)
- **Ctrl+D** (EOF)
- **SIGTERM** (termination)
- **SIGQUIT** (quit with core dump)

## Supported Applications

### 1. Replay Engine (`run_replay.py`)
```bash
python3 run_replay.py
# Press Ctrl+C to stop gracefully
```

### 2. Mid-Price Processor (`run_mid_price.py`)
```bash
python3 run_mid_price.py
# Press Ctrl+C to stop gracefully
```

### 3. Complete System (`start_system.py`)
```bash
python3 start_system.py
# Press Ctrl+C to stop both applications gracefully
```

### 4. Demo (`demo.py`)
```bash
python3 demo.py
# Press Ctrl+C to stop demo
```

### 5. Tests (`run_tests.py`)
```bash
python3 run_tests.py
# Press Ctrl+C to stop tests
```

## Signal Handling Features

### Graceful Shutdown Process
1. **Signal Reception**: Application receives SIGINT/SIGTERM
2. **Logging**: Signal is logged with details
3. **Task Cancellation**: All async tasks are properly cancelled
4. **Resource Cleanup**: 
   - Redis connections are closed
   - File buffers are flushed
   - Message queues are disconnected
5. **Exit**: Application exits with appropriate exit code

### Exit Codes
- **0**: Normal exit
- **1**: Application error
- **130**: Keyboard interrupt (Ctrl+C)

### Logging During Shutdown
```
{"signal": "SIGINT", "signum": 2, "event": "Received shutdown signal"}
{"event": "Starting graceful shutdown..."}
{"event": "Stopping replay application..."}
{"event": "Replay application stopped successfully"}
{"event": "Graceful shutdown completed"}
```

## Implementation Details

### SignalHandler Class
```python
from src.signal_handler import GracefulShutdown

shutdown_handler = GracefulShutdown()
signal.signal(signal.SIGINT, shutdown_handler.signal_handler)
```

### Async Signal Handling
```python
from src.signal_handler import AsyncSignalHandler

async_handler = AsyncSignalHandler(shutdown_callback=my_cleanup_function)
async_handler.setup(asyncio.get_event_loop())
```

### Decorators
```python
from src.signal_handler import handle_keyboard_interrupt

@handle_keyboard_interrupt
def my_function():
    # Function with automatic KeyboardInterrupt handling
    pass
```

## Best Practices

1. **Always use graceful shutdown** - Don't force kill applications
2. **Check logs** - Shutdown process is fully logged
3. **Wait for completion** - Allow applications to finish cleanup
4. **Use Ctrl+C** - Standard way to stop applications
5. **Monitor exit codes** - Check for proper shutdown

## Troubleshooting

### Application doesn't stop
- Wait a few seconds for graceful shutdown
- Check logs for shutdown progress
- Use `kill -TERM <pid>` for SIGTERM
- Use `kill -KILL <pid>` only as last resort

### Resources not cleaned up
- Check Redis connections: `redis-cli ping`
- Check file locks: `lsof | grep python`
- Restart Redis if needed: `brew services restart redis`

### Exit code 130
- Normal for Ctrl+C interruption
- Application stopped gracefully
- No action needed

## Testing Signal Handling

```bash
# Test Ctrl+C handling
python3 run_replay.py &
PID=$!
sleep 5
kill -INT $PID
wait $PID
echo "Exit code: $?"

# Test SIGTERM handling
python3 run_mid_price.py &
PID=$!
sleep 5
kill -TERM $PID
wait $PID
echo "Exit code: $?"
```

## Integration with Docker

Docker containers also support graceful shutdown:
```bash
docker-compose up
# Press Ctrl+C to stop all services gracefully
```

The signal handling works the same way in containerized environments.
