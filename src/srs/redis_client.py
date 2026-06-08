"""
Redis / Upstash client for SM-2+ Spaced Repetition System.

Supports both:
- Local Redis: redis://localhost:6379/0
- Upstash Redis: rediss://default:***@host.upstash.io:6379

Data model:
  HASH srs:card:{user_id}:{card_id} → CardState fields
  ZSET srs:queue:{user_id} → sorted by next_review_at
  HASH user:{user_id} → user profile data
  SET   user:lessons:{user_id} → completed lesson IDs
  STRING user:streak:{user_id} → current streak count
"""

import json
import time
import os
from typing import Optional

try:
    import redis as redis_mod
    from redis.exceptions import RedisError
except ImportError:
    redis_mod = None
    RedisError = Exception


# ─── Upstash REST API client (lightweight, no redis-py needed) ───


class UpstashRedisClient:
    """
    Upstash Redis REST API client.
    
    Uses Upstash's HTTP REST API — no TCP connections needed.
    Perfect for serverless environments (Vercel, Railway, etc.)
    
    Requires:
      UPSTASH_REDIS_REST_URL=https://<region>.upstash.io
      UPSTASH_REDIS_REST_TOKEN=<token>
      
    Or pass url/token directly.
    """
    
    def __init__(self, url: str = "", token: str = ""):
        import urllib.request
        self._request = urllib.request
        
        self.url = url or os.environ.get("UPSTASH_REDIS_REST_URL", "")
        self.token = token or os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
        
        if not self.url or not self.token:
            raise ValueError(
                "Upstash credentials required. Set UPSTASH_REDIS_REST_URL "
                "and UPSTASH_REDIS_REST_TOKEN env vars."
            )
        self._auth = f"Bearer {self.token}"
    
    def _cmd(self, command: str, *args) -> Optional[dict]:
        """Execute a Redis command via Upstash REST API."""
        import json as _json
        import base64
        
        payload = _json.dumps({
            "command": command,
            "args": list(args),
        }).encode()
        
        req = self._request.Request(
            self.url,
            data=payload,
            headers={
                "Authorization": self._auth,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        
        try:
            with self._request.urlopen(req, timeout=10) as resp:
                result = _json.loads(resp.read().decode())
                return result
        except Exception as e:
            print(f"[Upstash] Error: {e}")
            return None
    
    def hget(self, key: str, field: str) -> Optional[str]:
        r = self._cmd("HGET", key, field)
        if r and "result" in r:
            return r["result"]
        return None
    
    def hgetall(self, key: str) -> dict:
        r = self._cmd("HGETALL", key)
        if r and "result" in r:
            data = r["result"]
            # HGETALL returns flat list: [field1, val1, field2, val2, ...]
            return {data[i]: data[i+1] for i in range(0, len(data), 2)}
        return {}
    
    def hset(self, key: str, mapping: dict) -> bool:
        args = [key]
        for k, v in mapping.items():
            args.append(str(k))
            args.append(json.dumps(v) if not isinstance(v, str) else v)
        r = self._cmd("HSET", *args)
        return r is not None
    
    def zadd(self, key: str, score: float, member: str) -> bool:
        r = self._cmd("ZADD", key, str(score), member)
        return r is not None
    
    def zrangebyscore(self, key: str, min_v: float, max_v: float, 
                      limit: int = 20) -> list:
        r = self._cmd("ZRANGEBYSCORE", key, str(min_v), str(max_v),
                      "LIMIT", "0", str(limit))
        if r and "result" in r:
            return r["result"]
        return []
    
    def zrem(self, key: str, member: str) -> bool:
        r = self._cmd("ZREM", key, member)
        return r is not None
    
    def set(self, key: str, value: str, ex: int = 0) -> bool:
        if ex:
            r = self._cmd("SET", key, value, "EX", str(ex))
        else:
            r = self._cmd("SET", key, value)
        return r is not None
    
    def get(self, key: str) -> Optional[str]:
        r = self._cmd("GET", key)
        if r and "result" in r:
            return r["result"]
        return None
    
    def delete(self, key: str) -> bool:
        r = self._cmd("DEL", key)
        return r is not None
    
    def sadd(self, key: str, member: str) -> bool:
        r = self._cmd("SADD", key, member)
        return r is not None
    
    def srem(self, key: str, member: str) -> bool:
        r = self._cmd("SREM", key, member)
        return r is not None
    
    def smembers(self, key: str) -> set:
        r = self._cmd("SMEMBERS", key)
        if r and "result" in r:
            return set(r["result"])
        return set()
    
    def incr(self, key: str) -> Optional[int]:
        r = self._cmd("INCR", key)
        if r and "result" in r:
            try:
                return int(r["result"])
            except (ValueError, TypeError):
                return None
        return None
    
    def expire(self, key: str, seconds: int) -> bool:
        r = self._cmd("EXPIRE", key, str(seconds))
        return r is not None

    def ping(self) -> bool:
        r = self._cmd("PING")
        return r is not None and r.get("result") == "PONG"


# ─── Factory ───


def create_redis_client(redis_url: str = "") -> UpstashRedisClient:
    """
    Create appropriate Redis client based on URL.
    
    Priority:
    1. UPSTASH_REDIS_REST_URL env var → Upstash REST API
    2. REDIS_URL starting with 'rediss://' → Upstash (TLS)
    3. REDIS_URL starting with 'redis://' → local Redis
    4. Default → Upstash REST API (requires env vars)
    """
    rest_url = os.environ.get("UPSTASH_REDIS_REST_URL", "")
    rest_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
    
    if rest_url and rest_token:
        return UpstashRedisClient(url=rest_url, token=rest_token)
    
    # Fallback: try standard redis-py for local Redis
    if redis_mod and (not redis_url or redis_url.startswith("redis://")):
        url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        if url.startswith("redis://"):
            pool = redis_mod.ConnectionPool.from_url(
                url,
                max_connections=10,
                socket_timeout=5,
                socket_connect_timeout=3,
                retry_on_timeout=True,
                decode_responses=True,
            )
            return redis_mod.Redis(connection_pool=pool)
    
    # Try Upstash as last resort
    if rest_url and rest_token:
        return UpstashRedisClient(url=rest_url, token=rest_token)
    
    raise ValueError(
        "No Redis configuration found. "
        "Set UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN for Upstash, "
        "or REDIS_URL for local Redis."
    )


# ─── SRS Client (uses Upstash or Redis) ───


class SRSRedisClient:
    """SRS client that works with both Upstash REST API and local Redis."""
    
    def __init__(self, redis_url: str = ""):
        self.client = create_redis_client(redis_url)
    
    def _card_key(self, user_id: str, card_id: str) -> str:
        return f"srs:card:{user_id}:{card_id}"
    
    def _queue_key(self, user_id: str) -> str:
        return f"srs:queue:{user_id}"
    
    def get_card_state(self, user_id: str, card_id: str) -> Optional[dict]:
        return self.client.hgetall(self._card_key(user_id, card_id)) or None
    
    def save_card_state(self, user_id: str, card_id: str, state: dict):
        self.client.hset(self._card_key(user_id, card_id), state)
    
    def add_to_queue(self, user_id: str, card_id: str, next_review_at: float):
        self.client.zadd(self._queue_key(user_id), next_review_at, card_id)
    
    def get_review_queue(self, user_id: str, limit: int = 20) -> list:
        now = time.time()
        return self.client.zrangebyscore(
            self._queue_key(user_id), 0, now, limit
        )
    
    def remove_from_queue(self, user_id: str, card_id: str):
        self.client.zrem(self._queue_key(user_id), card_id)
    
    def health_check(self) -> bool:
        try:
            return self.client.ping()
        except Exception:
            return False
