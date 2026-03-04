from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SiteConfig:
    site_name: str
    site_url: str
    language: str
    niche: str


@dataclass
class SourcesConfig:
    rss_feeds: list[str]
    stackexchange: dict[str, Any]
    trends: dict[str, Any]
    priority_keywords: list[str]


class ConfigLoader:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.config_dir = root_dir / "config"

    def _load_yaml(self, name: str) -> dict[str, Any]:
        path = self.config_dir / name
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data

    def load_site(self) -> SiteConfig:
        data = self._load_yaml("site.yaml")
        site_url = data.get("site_url", "").strip()
        return SiteConfig(
            site_name=data.get("site_name", "SEO Autoblog Money"),
            site_url=site_url,
            language=data.get("language", "es"),
            niche=data.get("niche", "marketing digital"),
        )

    def load_sources(self) -> SourcesConfig:
        data = self._load_yaml("sources.yaml")
        return SourcesConfig(
            rss_feeds=data.get("rss_feeds", []),
            stackexchange=data.get("stackexchange", {}),
            trends=data.get("trends", {}),
            priority_keywords=data.get("priority_keywords", []),
        )

    def load_affiliates(self) -> dict[str, Any]:
        return self._load_yaml("affiliates.yaml")


def resolved_site_url(site_url: str, repo_name: str, github_repository: str | None = None) -> str:
    if site_url:
        return site_url.rstrip("/")

    if github_repository:
        owner, repo = github_repository.split("/")
        return f"https://{owner}.github.io/{repo}".rstrip("/")

    github_repo = os.getenv("GITHUB_REPOSITORY", "")
    if "/" in github_repo:
        owner, repo = github_repo.split("/")
        return f"https://{owner}.github.io/{repo}".rstrip("/")

    return f"https://example.github.io/{repo_name}".rstrip("/")
