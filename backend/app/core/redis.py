import logging
import time
from typing import Optional, Tuple
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from app.core.config import settings

logger = logging.getLogger("enermax.redis")


class RedisManager:
    """
    Production-grade Redis manager providing:
    - Connection pooling and keepalive
    - Strict namespaces with enforced TTL
    - Circuit breaker & graceful fallback to in-memory store when Redis is unavailable
    """

    def __init__(self):
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._is_connected: bool = False
        self._last_connect_attempt: float = 0.0
        self._reconnect_cooldown_seconds: float = 5.0
        # In-memory fallback store: {key: (value, expiry_timestamp)}
        self._fallback_store: dict[str, tuple[str, float]] = {}

    def _cleanup_fallback_store(self) -> None:
        """Evicts expired keys from in-memory fallback store."""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._fallback_store.items() if exp <= now]
        for k in expired_keys:
            self._fallback_store.pop(k, None)

    async def initialize(self) -> None:
        """Initializes connection pool."""
        try:
            self._pool = aioredis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT,
                decode_responses=True,
            )
            self._client = aioredis.Redis(connection_pool=self._pool)
            # Test ping
            await self._client.ping()
            self._is_connected = True
            logger.info("Connected to Redis successfully.")
        except Exception as exc:
            self._is_connected = False
            self._last_connect_attempt = time.time()
            logger.warning(
                f"Redis connection failed ({exc}). Operating in graceful in-memory fallback mode."
            )

    async def get_client(self) -> Optional[aioredis.Redis]:
        """Returns Redis client if available, attempting background reconnect if cooldown passed."""
        if self._client and self._is_connected:
            return self._client

        now = time.time()
        if now - self._last_connect_attempt > self._reconnect_cooldown_seconds:
            self._last_connect_attempt = now
            await self.initialize()

        return self._client if self._is_connected else None

    async def ping(self) -> bool:
        """Pings Redis and updates connection status."""
        try:
            client = await self.get_client()
            if client:
                res = await client.ping()
                self._is_connected = bool(res)
                return self._is_connected
        except Exception:
            self._is_connected = False
        return False

    async def close(self) -> None:
        """Closes Redis connections on shutdown."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._is_connected = False
        logger.info("Redis connection pool closed.")

    # -----------------------------------------------------------------------
    # Namespaced Key Builders
    # -----------------------------------------------------------------------
    @staticmethod
    def cache_key(tenant_id: str, entity: str, identifier: str) -> str:
        """Cache namespace: enermax:cache:{tenant_id}:{entity}:{identifier}"""
        return f"enermax:cache:{tenant_id}:{entity}:{identifier}"

    @staticmethod
    def session_key(user_id: str, token_jti: str) -> str:
        """Session namespace: enermax:session:{user_id}:{token_jti}"""
        return f"enermax:session:{user_id}:{token_jti}"

    @staticmethod
    def revocation_key(jti: str) -> str:
        """Token Revocation namespace: enermax:revocation:{jti}"""
        return f"enermax:revocation:{jti}"

    @staticmethod
    def ratelimit_key(scope: str, identifier: str) -> str:
        """Rate limit namespace: enermax:ratelimit:{scope}:{identifier}"""
        return f"enermax:ratelimit:{scope}:{identifier}"

    @staticmethod
    def job_key(tenant_id: str, job_id: str) -> str:
        """Background Job state namespace: enermax:job:{tenant_id}:{job_id}"""
        return f"enermax:job:{tenant_id}:{job_id}"

    # -----------------------------------------------------------------------
    # Resilient Cache Operations (Safe Fallback)
    # -----------------------------------------------------------------------
    async def get(self, key: str) -> Optional[str]:
        """Gets value from Redis with safe fallback to in-memory store."""
        client = await self.get_client()
        if client and self._is_connected:
            try:
                return await client.get(key)
            except (ConnectionError, TimeoutError, RedisError) as exc:
                logger.warning(f"Redis get({key}) error: {exc}. Falling back to memory.")
                self._is_connected = False

        self._cleanup_fallback_store()
        record = self._fallback_store.get(key)
        if record:
            val, exp = record
            if exp > time.time():
                return val
            self._fallback_store.pop(key, None)
        return None

    async def set(self, key: str, value: str, ttl_seconds: int = 300) -> bool:
        """Sets key with mandatory TTL in Redis with fallback to in-memory store."""
        if ttl_seconds <= 0:
            ttl_seconds = 300  # Enforce mandatory TTL

        client = await self.get_client()
        if client and self._is_connected:
            try:
                await client.setex(key, ttl_seconds, value)
                return True
            except (ConnectionError, TimeoutError, RedisError) as exc:
                logger.warning(f"Redis set({key}) error: {exc}. Falling back to memory.")
                self._is_connected = False

        self._cleanup_fallback_store()
        self._fallback_store[key] = (value, time.time() + ttl_seconds)
        return True

    async def delete(self, key: str) -> bool:
        """Deletes key from Redis and fallback store."""
        client = await self.get_client()
        if client and self._is_connected:
            try:
                await client.delete(key)
            except (ConnectionError, TimeoutError, RedisError) as exc:
                logger.warning(f"Redis delete({key}) error: {exc}.")
                self._is_connected = False

        self._fallback_store.pop(key, None)
        return True

    # -----------------------------------------------------------------------
    # Token Revocation Store
    # -----------------------------------------------------------------------
    async def revoke_token(self, jti: str, ttl_seconds: int) -> bool:
        """Revokes a JWT token by storing its jti until expiry."""
        key = self.revocation_key(jti)
        return await self.set(key, "revoked", ttl_seconds=ttl_seconds)

    async def is_token_revoked(self, jti: str) -> bool:
        """Checks if a JWT token jti is revoked."""
        key = self.revocation_key(jti)
        val = await self.get(key)
        return val == "revoked"

    # -----------------------------------------------------------------------
    # Rate Limiting Sliding Window (Redis + In-Memory Fallback)
    # -----------------------------------------------------------------------
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int]:
        """
        Fixed/sliding window rate limiter.
        Returns: (allowed: bool, current_count: int, retry_after: int)
        """
        now = time.time()
        client = await self.get_client()

        if client and self._is_connected:
            try:
                pipe = client.pipeline()
                pipe.incr(key)
                pipe.ttl(key)
                results = await pipe.execute()
                current_count = results[0]
                current_ttl = results[1]

                if current_count == 1 or current_ttl == -1:
                    await client.expire(key, window_seconds)
                    current_ttl = window_seconds

                allowed = current_count <= limit
                retry_after = max(current_ttl, 1) if not allowed else 0
                return allowed, current_count, retry_after
            except (ConnectionError, TimeoutError, RedisError) as exc:
                logger.warning(f"Redis rate limit check error: {exc}. Using fallback window.")
                self._is_connected = False

        # In-memory fallback
        self._cleanup_fallback_store()
        rec = self._fallback_store.get(key)
        if rec:
            raw_count, exp = rec
            count = int(raw_count) + 1
            ttl_left = max(1, int(exp - now))
            self._fallback_store[key] = (str(count), exp)
        else:
            count = 1
            ttl_left = window_seconds
            self._fallback_store[key] = (str(count), now + window_seconds)

        allowed = count <= limit
        retry_after = ttl_left if not allowed else 0
        return allowed, count, retry_after


# Global singleton instance
redis_manager = RedisManager()
