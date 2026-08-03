import os
import asyncpg
from typing import Optional

# Global pool instance
_pool: Optional[asyncpg.Pool] = None

async def init_db_pool(dsn: str = None) -> asyncpg.Pool:
    """
    Initializes the asyncpg connection pool.
    """
    global _pool
    if _pool is not None:
        return _pool
        
    if not dsn:
        dsn = os.getenv("DATABASE_URL", "postgres://postgres:root@localhost:5432/Lead_DB")
        
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
    return _pool

async def get_pool() -> asyncpg.Pool:
    """
    Retrieves the global connection pool. Raises RuntimeError if not initialized.
    """
    global _pool
    if _pool is None:
        raise RuntimeError("Database pool has not been initialized. Call init_db_pool first.")
    return _pool

async def close_db_pool():
    """
    Closes the global connection pool.
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
