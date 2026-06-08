"""
SM-2+ Spaced Repetition System Engine
Based on Piotr Wozniak's SM-2 algorithm (1987) with modern improvements.

Quality scale (0-5):
  5 = perfect response
  4 = correct after hesitation
  3 = correct with serious difficulty
  2 = incorrect, but answer seemed easy to recall
  1 = incorrect, but remembered upon seeing answer
  0 = complete blackout
"""

import math
import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CardState:
    """SRS state for a single flashcard."""
    ef: float = 2.5          # Easiness Factor (1.3 - 3.0)
    interval: int = 0        # Days until next review
    reps: int = 0            # Consecutive correct answers
    next_review_at: float = 0.0  # Unix timestamp (seconds)
    total_reviews: int = 0
    total_fails: int = 0
    last_quality: int = -1   # -1 = never reviewed


def sm2(card: CardState, quality: int) -> CardState:
    """
    Apply SM-2 algorithm and return updated CardState.
    
    Args:
        card: Current card state
        quality: User's self-assessed recall quality (0-5)
    
    Returns:
        Updated CardState with new scheduling
    """
    new = CardState(
        ef=card.ef,
        interval=card.interval,
        reps=card.reps,
        next_review_at=card.next_review_at,
        total_reviews=card.total_reviews + 1,
        total_fails=card.total_fails + (1 if quality < 3 else 0),
        last_quality=quality,
    )
    
    if quality < 3:
        # Failed — reset repetition count
        new.reps = 0
        new.interval = 1  # Review again tomorrow
    else:
        # Passed
        if new.reps == 0:
            new.interval = 1
        elif new.reps == 1:
            new.interval = 6
        else:
            new.interval = round(new.interval * new.ef)
        new.reps += 1
    
    # Update Easiness Factor (SM-2 formula)
    new.ef = card.ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new.ef = max(1.3, min(3.0, new.ef))  # Clamp to [1.3, 3.0]
    
    # Fuzz factor: ±5% random variation to prevent card clumping
    fuzz = 0.95 + random.random() * 0.1
    new.interval = max(1, round(new.interval * fuzz))
    
    # Cap max interval at 365 days
    new.interval = min(new.interval, 365)
    
    # Set next review timestamp
    new.next_review_at = time.time() + new.interval * 86400
    
    return new


def get_due_cards(cards: list[tuple[str, CardState]], limit: int = 20) -> list[tuple[str, CardState]]:
    """
    Filter cards that are due for review, sorted by urgency.
    
    Args:
        cards: List of (card_id, CardState) tuples
        limit: Max number of cards to return
    
    Returns:
        Due cards sorted by next_review_at (most overdue first)
    """
    now = time.time()
    due = [(cid, cs) for cid, cs in cards if cs.next_review_at <= now]
    due.sort(key=lambda x: x[1].next_review_at)
    return due[:limit]


def get_new_cards_for_today(
    mastered_count: int,
    target_new_per_day: int = 10,
    max_total_reviews: int = 50,
) -> int:
    """
    Calculate how many new cards to introduce today.
    
    Args:
        mastered_count: Cards already learned today
        target_new_per_day: Desired new cards per day
        max_total_reviews: Max reviews per day (new + review)
    
    Returns:
        Number of new cards to show
    """
    available = target_new_per_day - mastered_count
    return max(0, min(available, max_total_reviews))
