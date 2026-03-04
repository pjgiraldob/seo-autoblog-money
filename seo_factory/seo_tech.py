from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape


def build_robots(site_url: str) -> str:
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        f"Sitemap: {site_url}/sitemap.xml",
    ]
    return "\n".join(lines)


def build_sitemap(site_url: str, entries: Iterable[dict[str, str]]) -> str:
    now = datetime.now(timezone.utc).date().isoformat()
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
    ]
    for entry in entries:
        loc = f"{site_url}/{entry['path'].lstrip('/')}"
        lastmod = entry.get("date", now)
        lines.extend(
            [
                "  <url>",
                f"    <loc>{escape(loc)}</loc>",
                f"    <lastmod>{escape(lastmod)}</lastmod>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return "\n".join(lines)


def build_rss(site_url: str, site_name: str, entries: Iterable[dict[str, str]]) -> str:
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\">",
        "  <channel>",
        f"    <title>{escape(site_name)}</title>",
        f"    <link>{escape(site_url)}</link>",
        "    <description>Publicaciones SEO automatizadas</description>",
        f"    <lastBuildDate>{now}</lastBuildDate>",
    ]
    for entry in entries:
        loc = f"{site_url}/{entry['path'].lstrip('/')}"
        lines.extend(
            [
                "    <item>",
                f"      <title>{escape(entry['title'])}</title>",
                f"      <link>{escape(loc)}</link>",
                f"      <guid>{escape(loc)}</guid>",
                f"      <pubDate>{escape(entry.get('pub_rss', now))}</pubDate>",
                f"      <description>{escape(entry.get('description', ''))}</description>",
                "    </item>",
            ]
        )
    lines.extend(["  </channel>", "</rss>"])
    return "\n".join(lines)


def write_text(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
