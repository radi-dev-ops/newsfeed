"""RSS feed fetching utilities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional
import calendar
import logging
import time

import feedparser

from .config import FeedConfig

logger = logging.getLogger(__name__)


def _struct_time_to_datetime(value: time.struct_time) -> datetime:
    return datetime.fromtimestamp(calendar.timegm(value), tz=timezone.utc)


@dataclass(slots=True)
class Article:
    feed_id: str
    feed_name: str
    title: str
    link: str
    summary: Optional[str]
    published: datetime


def fetch_feed(feed: FeedConfig) -> feedparser.FeedParserDict:
    """Fetch and parse a feed."""
    logger.debug("Fetching feed %s", feed.url)
    return feedparser.parse(feed.url)


def _extract_published(entry: feedparser.FeedParserDict) -> Optional[datetime]:
    candidate: Optional[time.struct_time] = entry.get("published_parsed") or entry.get("updated_parsed")
    if candidate is None:
        return None
    return _struct_time_to_datetime(candidate)


def collect_articles(
    feeds: Iterable[FeedConfig],
    lookback: timedelta,
    now: Optional[datetime] = None,
) -> List[Article]:
    """Fetch new articles from the configured feeds within the lookback window."""

    now = now or datetime.now(timezone.utc)
    articles: list[Article] = []
    seen_links: set[str] = set()

    for feed in feeds:
        parsed = fetch_feed(feed)
        if parsed.bozo:
            logger.warning("Feed %s returned errors: %s", feed.url, parsed.bozo_exception)
        for entry in parsed.entries:
            published = _extract_published(entry)
            if published is None or now - published > lookback:
                continue
            link = entry.get("link")
            if not link:
                continue
            if link in seen_links:
                continue
            seen_links.add(link)
            articles.append(
                Article(
                    feed_id=feed.id,
                    feed_name=feed.name,
                    title=entry.get("title", "Untitled"),
                    link=link,
                    summary=entry.get("summary"),
                    published=published,
                )
            )

    articles.sort(key=lambda article: article.published, reverse=True)
    return articles


__all__ = ["Article", "collect_articles"]
