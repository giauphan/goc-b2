"""
Redis client for SM-2+ Spaced Repetition System.

Data model:
  HASH srs:card:{user_id}:{card_id} → CardState fields
  ZSET srs:queue:{user_id} → sorted by next_review_at
  HASH user:{user_id} → user profile data
  SET   user:lessons:{user_id} → completed lesson IDs
  STRING user:streak:{user_id} → current streak count
"""

import json
import time
from typing import Optional

try:
    import redis as redis_mod
    from redis.exceptions import RedisError
except ImportError:
    redis_mod = None
    RedisError = Exception


class SRSRedisClient:
    """Redis-backed SRS client with SM-2 engine integration."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        if redis_mod is None:
            raise ImportError("redis package not installed. Run: pip install redis")
        
        self.pool = redis_mod.ConnectionPool.from_url(
            redis_url,
            max_connections=10,
            socket_timeout=5,
            socket_connect_timeout=3,
            retry_on_timeout=True,
            decode_responses=True,
        )
        self.redis = redis_mod.Redis(connection_pool=self.pool)
    
    # ── Card State ────────────────────────────────────────────
    
    def _card_key(self, user_id: str, card_id: str) -> str:
        return f"srs:card:{user_id}:{card_id}"
    
    def _queue_key(self, user_id: str) -> str:
        return f"srs:queue:{user_id}"
    
    def get_card_state(self, user_id: str, card_id: str) -> Optional[dict]:
        """Get SRS state for a user's card."""
        data = self.redis.hgetall(self._card_key(user_id, card_id))
        if not data:
            return None
        # Convert numeric fields
        for field in ("ef", "interval", "reps", "next_review_at",
                      "total_reviews", "total_fails", "last_quality"):
            if field in data:
                try:
                    data[field] = float(data[field]) if field == "ef" else int(data[field])
                except (ValueError, TypeError):
                    data[field] = 0
        return data
    
    def save_card_state(self, user_id: str, card_id: str, state: dict):
        """Save SRS state for a user's card."""
        self.redis.hset(self._card_key(user_id, card_id), mapping=state)
    
    # ── Review Queue ──────────────────────────────────────────
    
    def get_review_queue(self, user_id: str, limit: int = 20) -> list[str]:
        """Get cards due for review (most overdue first)."""
        now = time.time()
        cards = self.redis.zrangebyscore(
            self._queue_key(user_id),
            0, now,
            start=0, num=limit,
        )
        return cards
    
    def add_to_queue(self, user_id: str, card_id: str, next_review_at: float):
        """Add/update card in review queue."""
        self.redis.zadd(self._queue_key(user_id), {card_id: next_review_at})
    
    def remove_from_queue(self, user_id: str, card_id: str):
        """Remove card from review queue (e.g., mastered)."""
        self.redis.zrem(self._queue_key(user_id), card_id)
    
    def get_queue_count(self, user_id: str) -> dict:
        """Get queue stats."""
        now = time.time()
        total = self.redis.zcard(self._queue_key(user_id))
        due = self.redis.zcount(self._queue_key(user_id), 0, now)
        return {"total": total, "due": due}
    
    # ── User Progress ─────────────────────────────────────────
    
    def _user_key(self, user_id: str) -> str:
        return f"user:{user_id}"
    
    def get_user(self, user_id: str) -> Optional[dict]:
        data = self.redis.hgetall(self._user_key(user_id))
        return data if data else None
    
    def create_user(self, user_id: str, name: str = ""):
        """Create a new user profile."""
        self.redis.hset(self._user_key(user_id), mapping={
            "name": name,
            "level": "A1",
            "total_xp": "0",
            "streak_days": "0",
            "daily_goal": "20",
            "created_at": str(time.time()),
        })
    
    def update_user_xp(self, user_id: str, xp_gained: int):
        """Add XP to user."""
        self.redis.hincrby(self._user_key(user_id), "total_xp", xp_gained)
    
    def get_streak(self, user_id: str) -> int:
        """Get current streak days."""
        val = self.redis.get(f"user:streak:{user_id}")
        return int(val) if val else 0
    
    def update_streak(self, user_id: str):
        """Update streak (call once per day when user completes a review)."""
        today = int(time.time() / 86400)
        last_active = self.redis.get(f"user:last_active:{user_id}")
        
        if last_active is None:
            # First activity
            self.redis.set(f"user:streak:{user_id}", 1)
        else:
            last_day = int(last_active)
            if last_day == today:
                pass  # Already counted today
            elif last_day == today - 1:
                # Consecutive day
                self.redis.incr(f"user:streak:{user_id}")
            else:
                # Streak broken
                self.redis.set(f"user:streak:{user_id}", 1)
        
        self.redis.set(f"user:last_active:{user_id}", today)
    
    # ── Lessons ───────────────────────────────────────────────
    
    def complete_lesson(self, user_id: str, lesson_id: str):
        """Mark a lesson as completed."""
        self.redis.sadd(f"user:lessons:{user_id}", lesson_id)
    
    def get_completed_lessons(self, user_id: str) -> set:
        return self.redis.smembers(f"user:lessons:{user_id}")
    
    def is_lesson_completed(self, user_id: str, lesson_id: str) -> bool:
        return self.redis.sismember(f"user:lessons:{user_id}", lesson_id)
    
    # ── Health ────────────────────────────────────────────────
    
    def ping(self) -> bool:
        try:
            return self.redis.ping()
        except RedisError:
            return False
    
    def get_stats(self) -> dict:
        info = self.redis.info()
        return {
            "version": info.get("redis_version", ""),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", ""),
            "hit_rate": self._calc_hit_rate(info),
            "ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
        }
    
    @staticmethod
    def _calc_hit_rate(info: dict) -> float:
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return round(hits / total * 100, 1) if total > 0 else 0.0
    
    def close(self):
        self.redis.close()
        self.pool.disconnect()
