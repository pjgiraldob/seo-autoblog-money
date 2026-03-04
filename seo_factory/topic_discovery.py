from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import feedparser
import requests

logger = logging.getLogger(__name__)


@dataclass
class Topic:
    title: str
    source: str
    keywords: list[str]
    summary: str
    published_at: str
    score: int


def _extract_keywords(text: str) -> list[str]:
    words = [w.strip(" ,.!?:;()[]\"'").lower() for w in text.split()]
    words = [w for w in words if len(w) > 3 and w.isascii()]
    unique = []
    for word in words:
        if word not in unique:
            unique.append(word)
        if len(unique) >= 8:
            break
    return unique


def _score_topic(title: str, summary: str, priority_keywords: list[str]) -> int:
    text = f"{title} {summary}".lower()
    score = 1
    for keyword in priority_keywords:
        if keyword.lower() in text:
            score += 5
    score += min(len(title.split()), 12)
    return score


def discover_from_rss(feeds: list[str], priority_keywords: list[str], limit: int) -> list[Topic]:
    topics: list[Topic] = []
    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as exc:
            logger.warning("RSS error for %s: %s", feed_url, exc)
            continue

        for entry in parsed.entries[: max(5, limit)]:
            title = entry.get("title", "Tema SEO")
            summary = entry.get("summary", "") or entry.get("description", "")
            published = entry.get("published", datetime.now(timezone.utc).date().isoformat())
            keywords = _extract_keywords(f"{title} {summary}")
            score = _score_topic(title, summary, priority_keywords)
            topics.append(
                Topic(
                    title=title,
                    source=f"rss:{feed_url}",
                    keywords=keywords,
                    summary=summary[:300],
                    published_at=published,
                    score=score,
                )
            )

    topics.sort(key=lambda t: t.score, reverse=True)
    return topics[:limit]


def discover_from_stackexchange(stack_cfg: dict[str, Any], priority_keywords: list[str], limit: int) -> list[Topic]:
    site = stack_cfg.get("site", "webmasters")
    tags = ";".join(stack_cfg.get("tags", ["seo"]))
    url = "https://api.stackexchange.com/2.3/questions"
    params = {
        "order": "desc",
        "sort": "votes",
        "site": site,
        "tagged": tags,
        "pagesize": max(10, limit),
    }

    topics: list[Topic] = []
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        logger.warning("StackExchange API error: %s", exc)
        return topics

    for item in payload.get("items", [])[:limit]:
        title = item.get("title", "Pregunta SEO")
        tags_list = item.get("tags", [])
        summary = f"Pregunta popular en {site} sobre {', '.join(tags_list)}"
        score = _score_topic(title, summary, priority_keywords) + int(item.get("score", 0))
        topics.append(
            Topic(
                title=title,
                source=f"stackexchange:{site}",
                keywords=tags_list[:8],
                summary=summary,
                published_at=datetime.fromtimestamp(item.get("creation_date", 0), tz=timezone.utc).date().isoformat(),
                score=score,
            )
        )

    topics.sort(key=lambda t: t.score, reverse=True)
    return topics[:limit]


def discover_from_trends(trends_cfg: dict[str, Any], priority_keywords: list[str], limit: int) -> list[Topic]:
    if not trends_cfg.get("enabled", False):
        return []

    try:
        from pytrends.request import TrendReq
    except Exception:
        logger.warning("pytrends is not available, continuing without trends")
        return []

    geo = trends_cfg.get("geo", "ES")
    topics: list[Topic] = []
    try:
        pytrends = TrendReq(hl="es-ES", tz=0)
        trending = pytrends.trending_searches(pn=geo)
    except Exception as exc:
        logger.warning("pytrends request failed: %s", exc)
        return []

    for idx, value in enumerate(trending[0].head(limit).tolist()):
        title = f"Tendencia SEO: {value}"
        summary = f"Como aprovechar la tendencia '{value}' para contenido evergreen y trafico organico"
        score = _score_topic(title, summary, priority_keywords) + (limit - idx)
        topics.append(
            Topic(
                title=title,
                source="pytrends",
                keywords=_extract_keywords(value),
                summary=summary,
                published_at=datetime.now(timezone.utc).date().isoformat(),
                score=score,
            )
        )
    return topics


def discover_topics(sources_cfg: Any, limit: int) -> list[Topic]:
    candidates: list[Topic] = []
    candidates.extend(discover_from_rss(sources_cfg.rss_feeds, sources_cfg.priority_keywords, limit * 2))
    candidates.extend(discover_from_stackexchange(sources_cfg.stackexchange, sources_cfg.priority_keywords, limit * 2))
    candidates.extend(discover_from_trends(sources_cfg.trends, sources_cfg.priority_keywords, limit))

    deduped: dict[str, Topic] = {}
    for topic in candidates:
        key = topic.title.lower().strip()
        if key not in deduped or topic.score > deduped[key].score:
            deduped[key] = topic

    ordered = sorted(deduped.values(), key=lambda t: t.score, reverse=True)
    return ordered[:limit]
