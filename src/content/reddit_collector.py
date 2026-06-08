"""
Reddit content module for English learning.

Uses Reddit's OAuth2 API. Requires:
  1. Reddit App credentials (client_id, client_secret)
     - Get at https://www.reddit.com/prefs/apps
  2. User Agent (required by Reddit API)

Note: Reddit's public .json API was blocked in 2023.
All API access now requires OAuth2 authentication.

API: GET https://oauth.reddit.com/r/{subreddit}/{endpoint}
Auth: OAuth2 client credentials grant
"""

import json
import time
import logging
import os
from dataclasses import dataclass, field
from typing import Optional
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

# Reddit OAuth2 endpoints
REDDIT_OAUTH_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_URL = "https://oauth.reddit.com"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# Target subreddits for English learning
ENGLISH_LEARNING_SUBREDDITS = [
    "EnglishLearning",      # Main: Q&A for learners
    "English",              # Grammar/vocab discussions
    "languagelearning",     # General language learning tips
    "EnglishGrammar",       # Focused grammar help
    "Vocabulary",           # Word learning
    "WriteStreakEN",        # Writing practice
    "EnglishPractice",      # Practice posts
    "grammar",              # Grammar questions
]

# Content types to fetch
CONTENT_TYPES = ["hot", "new", "top", "rising"]


@dataclass
class RedditPost:
    """Structured Reddit post for English learning."""
    post_id: str
    title: str
    selftext: str
    subreddit: str
    author: str
    score: int
    num_comments: int
    created_utc: float
    url: str
    permalink: str
    over_18: bool = False
    is_self: bool = True
    comments: list = field(default_factory=list)
    analysis: dict = field(default_factory=dict)


class RedditAPIClient:
    """Minimal Reddit API client following yt-dlp's .json pattern."""
    
    def __init__(self, user_agent: str = USER_AGENT,
                 client_id: str = "", client_secret: str = ""):
        self.user_agent = user_agent
        self.client_id = client_id or os.environ.get("REDDIT_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("REDDIT_CLIENT_SECRET", "")
        self.access_token = ""
        self.token_expires = 0.0
        self.last_request = 0.0
        self.min_interval = 2.0  # 2s between requests (rate limiting)
    
    def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token via client credentials grant."""
        if self.access_token and time.time() < self.token_expires:
            return self.access_token
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit OAuth2 credentials not configured. "
                          "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET env vars.")
            return None
        
        data = urlencode({"grant_type": "client_credentials"}).encode()
        req = Request(REDDIT_OAUTH_URL, data=data,
                     headers={"User-Agent": self.user_agent})
        import base64
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        req.add_header("Authorization", f"Basic {auth}")
        
        try:
            with urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
                self.access_token = result.get("access_token", "")
                self.token_expires = time.time() + result.get("expires_in", 3600) - 60
                return self.access_token
        except HTTPError as e:
            logger.error(f"Reddit OAuth failed: {e.code}")
            return None
    
    def _rate_limit(self):
        """Ensure we don't exceed Reddit's rate limits."""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
    
    def _request(self, url: str) -> Optional[dict]:
        """Make authenticated HTTP request to Reddit OAuth2 API."""
        token = self._get_access_token()
        if not token:
            logger.error("No Reddit access token — skipping request")
            return None
        
        self._rate_limit()
        req = Request(url, headers={
            "User-Agent": self.user_agent,
            "Authorization": f"Bearer {token}",
        })
        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            logger.error(f"Reddit API error {e.code}: {url}")
            if e.code == 429:
                # Rate limited - wait longer
                retry_after = int(e.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited, waiting {retry_after}s...")
                time.sleep(retry_after)
                return None
            return None
        except (URLError, json.JSONDecodeError, OSError) as e:
            logger.error(f"Reddit request failed: {e}")
            return None
    
    def get_subreddit_posts(
        self, subreddit: str, content_type: str = "hot", limit: int = 25
    ) -> list[RedditPost]:
        """Fetch posts from a subreddit using OAuth2 API.
        URL: https://oauth.reddit.com/r/{subreddit}/{content_type}
        """
        url = f"{REDDIT_API_URL}/r/{subreddit}/{content_type}?limit={limit}"
        data = self._request(url)
        if not data:
            return []
        
        posts = []
        for child in data.get("data", {}).get("children", []):
            if child.get("kind") != "t3":  # t3 = post
                continue
            post_data = child.get("data", {})
            
            # Skip stickied posts
            if post_data.get("stickied"):
                continue
            
            post = RedditPost(
                post_id=post_data.get("id", ""),
                title=post_data.get("title", ""),
                selftext=post_data.get("selftext", ""),
                subreddit=post_data.get("subreddit", ""),
                author=post_data.get("author", "[deleted]"),
                score=post_data.get("score", 0),
                num_comments=post_data.get("num_comments", 0),
                created_utc=post_data.get("created_utc", 0),
                url=post_data.get("url", ""),
                permalink=f"https://www.reddit.com{post_data.get('permalink', '')}",
                over_18=post_data.get("over_18", False),
                is_self=post_data.get("is_self", True),
            )
            posts.append(post)
        
        return posts
    
    def get_post_comments(self, subreddit: str, post_id: str, limit: int = 50) -> list[dict]:
        """Fetch comments for a post via OAuth2 API.
        URL: https://oauth.reddit.com/r/{subreddit}/comments/{post_id}
        """
        url = f"{REDDIT_API_URL}/r/{subreddit}/comments/{post_id}?limit={limit}"
        data = self._request(url)
        if not data or len(data) < 2:
            return []
        
        comments = []
        self._extract_comments(data[1], comments)
        return comments
    
    def _extract_comments(self, data: dict, result: list, depth: int = 0):
        """Recursively extract comments from Reddit's nested JSON."""
        if depth > 5:  # Limit nesting depth
            return
        
        for child in data.get("data", {}).get("children", []):
            if child.get("kind") != "t1":  # t1 = comment
                continue
            comment_data = child.get("data", {})
            result.append({
                "id": comment_data.get("id", ""),
                "author": comment_data.get("author", "[deleted]"),
                "body": comment_data.get("body", ""),
                "score": comment_data.get("score", 0),
                "created_utc": comment_data.get("created_utc", 0),
                "depth": depth,
                "replies": comment_data.get("replies", {}),
            })
            
            # Handle nested replies
            replies = comment_data.get("replies")
            if isinstance(replies, dict):
                self._extract_comments(replies, result, depth + 1)


class EnglishLearningContentCollector:
    """Collect and structure English learning content from Reddit."""
    
    def __init__(self):
        self.api = RedditAPIClient()
    
    def collect_qa_posts(self, limit_per_sub: int = 10) -> list[dict]:
        """Collect Q&A posts useful for English learners.
        
        Returns structured content with:
        - Question title (learning topic)
        - Body text (reading material)
        - Top comments (correct answers/explanations)
        - Vocabulary highlights
        """
        results = []
        
        for subreddit in ENGLISH_LEARNING_SUBREDDITS[:3]:  # Top 3 subs
            posts = self.api.get_subreddit_posts(subreddit, "hot", limit_per_sub)
            
            for post in posts:
                if post.over_18 or not post.selftext:
                    continue
                
                # Skip very short or very long posts
                text_length = len(post.selftext)
                if text_length < 20 or text_length > 5000:
                    continue
                
                entry = {
                    "source": "reddit",
                    "subreddit": post.subreddit,
                    "title": post.title,
                    "body": post.selftext,
                    "url": post.permalink,
                    "author": post.author,
                    "score": post.score,
                    "comments_count": post.num_comments,
                    "topics": self._extract_topics(post.title, post.selftext),
                    "vocabulary": [],
                    "grammar_points": [],
                    "difficulty_level": self._estimate_difficulty(post.selftext),
                }
                
                results.append(entry)
        
        # Sort by score (quality signal)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:20]  # Top 20
    
    def _extract_topics(self, title: str, body: str) -> list[str]:
        """Extract learning topics from post content."""
        topics = []
        text = (title + " " + body).lower()
        
        topic_keywords = {
            "grammar": ["grammar", "tense", "verb", "noun", "adjective", "preposition",
                       "article", "conjunction", "sentence structure"],
            "vocabulary": ["vocabulary", "word", "meaning", "definition", "synonym",
                          "antonym", "phrase", "idiom"],
            "pronunciation": ["pronunciation", "pronounce", "accent", "sound", "speak",
                            "phonetic", "intonation"],
            "writing": ["writing", "essay", "paragraph", "composition", "write"],
            "listening": ["listening", "hear", "audio", "podcast", "video"],
            "speaking": ["speaking", "conversation", "fluency", "speak", "talk"],
            "reading": ["reading", "read", "comprehension", "text", "article"],
            "exam": ["ielts", "toefl", "toeic", "exam", "test", "cambridge"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)
        
        return topics if topics else ["general"]
    
    def _estimate_difficulty(self, text: str) -> str:
        """Estimate CEFR difficulty level based on text complexity."""
        words = text.split()
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
        
        if avg_word_len < 4.5:
            return "A1"
        elif avg_word_len < 5.0:
            return "A2"
        elif avg_word_len < 5.5:
            return "B1"
        else:
            return "B2"


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = EnglishLearningContentCollector()
    
    print("=== English Learning Content from Reddit ===\n")
    
    posts = collector.collect_qa_posts(limit_per_sub=5)
    for i, post in enumerate(posts[:5], 1):
        print(f"{i}. [{post['subreddit']}] {post['title']}")
        print(f"   Topics: {', '.join(post['topics'])}")
        print(f"   Difficulty: {post['difficulty_level']}")
        print(f"   Score: {post['score']} | Comments: {post['comments_count']}")
        print(f"   URL: {post['url']}")
        print(f"   Body: {post['body'][:200]}...")
        print()
