import asyncio
import os
from datetime import datetime
from uuid import uuid4

import pytest

from src.message_queue import MessageQueue
from src.models import TradingMessage

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("RELAY_REDIS_TEST_URL"),
        reason="RELAY_REDIS_TEST_URL is not configured",
    ),
]


@pytest.mark.asyncio
async def test_redis_stream_publish_consume_round_trip():
    suffix = uuid4().hex
    queue = MessageQueue(
        redis_url=os.environ["RELAY_REDIS_TEST_URL"],
        stream_name=f"neozork:relay:test:{suffix}",
        consumer_group=f"integration:{suffix}",
    )
    expected = TradingMessage(
        index=1,
        timestamp=datetime.now(),
        ticker="BTCUSDT",
        ask_amount=1,
        ask_price=101,
        bid_price=99,
        bid_amount=2,
        latency=1,
    )
    await queue.connect()
    try:
        await queue.publish(expected)
        observed = await asyncio.wait_for(anext(queue.consume(count=1, block=100)), timeout=2)
        assert observed == expected
    finally:
        await queue.clear_queue()
        await queue.disconnect()
