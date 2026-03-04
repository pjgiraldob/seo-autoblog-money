from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class StateRecord:
    slug: str
    title: str
    date: str
    path: str
    tags: list[str]
    categories: list[str]


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save({"published": {}})

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"published": {}}
        with self.path.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if "published" not in data:
            data["published"] = {}
        return data

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def has_slug(self, slug: str) -> bool:
        data = self.load()
        return slug in data.get("published", {})

    def add_post(self, record: StateRecord) -> None:
        data = self.load()
        published = data.setdefault("published", {})
        if record.slug in published:
            return
        published[record.slug] = {
            "title": record.title,
            "date": record.date,
            "path": record.path,
            "tags": record.tags,
            "categories": record.categories,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save(data)

    def count_posts_on_date(self, date_str: str) -> int:
        data = self.load()
        published = data.get("published", {})
        total = 0
        for item in published.values():
            record_date = str(item.get("date", "")).strip()
            if record_date == date_str:
                total += 1
        return total


def normalize_text(value: str) -> str:
    raw = unicodedata.normalize("NFKD", value)
    no_accents = "".join(ch for ch in raw if not unicodedata.combining(ch))
    lowered = no_accents.lower()
    cleaned = re.sub(r"[^a-z0-9\s-]", "", lowered)
    compact = re.sub(r"\s+", " ", cleaned).strip()
    return compact


def slugify(value: str) -> str:
    normalized = normalize_text(value)
    slug = re.sub(r"[\s_]+", "-", normalized)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "post"

