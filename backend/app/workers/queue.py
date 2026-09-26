from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import get_settings


async def enqueue_message_processing(message_id: str) -> bool:
    redis_url = get_settings().redis_url
    if not redis_url:
        return False

    pool: ArqRedis = await create_pool(RedisSettings.from_dsn(redis_url))
    try:
        await pool.enqueue_job("process_message", message_id)
        return True
    finally:
        await pool.close()
