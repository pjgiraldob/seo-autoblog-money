from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ConfigLoader, resolved_site_url
from .content_generator import generate_article
from .monetization import recommendations_markdown, select_affiliate_items
from .seo_tech import build_robots, build_rss, build_sitemap, write_text
from .social_snippets import make_social_snippets
from .storage import StateRecord, StateStore, slugify
from .topic_discovery import discover_topics

logger = logging.getLogger(__name__)


def _parse_frontmatter(md_text: str) -> dict[str, Any]:
    if not md_text.startswith("---\n"):
        return {}
    parts = md_text.split("---\n", 2)
    if len(parts) < 3:
        return {}
    raw = parts[1]
    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"")
    return data


def _load_existing_posts(docs_dir: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for folder in [docs_dir / "posts", docs_dir / "guides"]:
        folder.mkdir(parents=True, exist_ok=True)
        for md in folder.glob("*.md"):
            text = md.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            if not fm:
                continue
            fm["path"] = str(md.relative_to(docs_dir)).replace("\\", "/")
            fm["title"] = fm.get("title", md.stem)
            entries.append(fm)
    return entries


def _frontmatter_to_yaml(frontmatter: dict[str, Any]) -> str:
    lines = ["---"]
    for key in ["title", "slug", "date", "description", "tags", "categories", "canonical"]:
        value = frontmatter.get(key)
        if isinstance(value, list):
            quoted = ", ".join(f'"{v}"' for v in value)
            lines.append(f"{key}: [{quoted}]")
        else:
            lines.append(f"{key}: \"{value}\"")
    lines.append("---")
    return "\n".join(lines)


def _related_links(current_tags: list[str], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in existing:
        tags_raw = item.get("tags", "")
        if isinstance(tags_raw, str):
            tags = [t.strip().strip("[]\"") for t in tags_raw.split(",") if t.strip()]
        else:
            tags = tags_raw
        overlap = len(set(t.lower() for t in current_tags) & set(t.lower() for t in tags))
        scored.append((overlap, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:2]]


def _ensure_pillar_guide(docs_dir: Path, niche: str, site_url: str, dry_run: bool) -> dict[str, Any]:
    guides_dir = docs_dir / "guides"
    guides_dir.mkdir(parents=True, exist_ok=True)
    existing = list(guides_dir.glob("*.md"))
    if existing:
        first = existing[0]
        return {"title": first.stem.replace("-", " ").title(), "path": f"guides/{first.name}"}

    slug = slugify(f"guia-pilar-{niche}")
    canonical = f"{site_url}/guides/{slug}/"
    frontmatter = {
        "title": f"Guia Pilar de {niche.title()}",
        "slug": slug,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "description": "Guia evergreen para construir una base SEO sostenible en este nicho.",
        "tags": ["guia", "pilar", "seo"],
        "categories": ["guides"],
        "canonical": canonical,
    }
    body = (
        "# Guia Pilar\n\n"
        "Esta guia resume fundamentos evergreen del nicho: arquitectura, contenidos y conversion.\n\n"
        "## Fundamentos\n"
        "Define publico, intencion de busqueda y oferta principal.\n\n"
        "## Arquitectura\n"
        "Agrupa contenidos por clusters y usa enlaces internos consistentes.\n\n"
        "## Publicacion\n"
        "Publica con cadencia estable y revisa rendimiento de forma mensual."
    )
    content = _frontmatter_to_yaml(frontmatter) + "\n\n" + body
    path = guides_dir / f"{slug}.md"
    if not dry_run:
        path.write_text(content, encoding="utf-8")
    return {"title": frontmatter["title"], "path": f"guides/{slug}.md"}


def _newsletter_block(newsletter_form_url: str | None, newsletter_email: str | None) -> str:
    if newsletter_form_url:
        return (
            "## Suscripcion\n\n"
            f"[Suscribirme]({newsletter_form_url}) para recibir nuevas guias y plantillas SEO."
        )
    mailto_target = newsletter_email.strip() if newsletter_email else ""
    return (
        "## Suscripcion\n\n"
        "Si quieres nuevas guias por email, escribe a "
        f"[este correo](mailto:{mailto_target}?subject=Alta%20newsletter) "
        "o revisa [como suscribirte](../newsletter/index.md)."
    )


def _lead_magnet_block() -> str:
    return (
        "## Recurso gratis\n\n"
        "Descarga la plantilla de plan editorial semanal en "
        "[recursos gratis](../assets/lead-magnet.md)."
    )


def generate_posts(root_dir: Path, limit: int, dry_run: bool = False) -> list[dict[str, Any]]:
    config_loader = ConfigLoader(root_dir)
    site_cfg = config_loader.load_site()
    sources_cfg = config_loader.load_sources()
    affiliates_cfg = config_loader.load_affiliates()

    repo_name = root_dir.name
    site_url = resolved_site_url(site_cfg.site_url, repo_name)

    state = StateStore(root_dir / "state" / "state.json")
    docs_dir = root_dir / "docs"
    posts_dir = docs_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    existing = _load_existing_posts(docs_dir)
    pillar = _ensure_pillar_guide(docs_dir, site_cfg.niche, site_url, dry_run)

    topics = discover_topics(sources_cfg, limit * 4)
    created: list[dict[str, Any]] = []

    newsletter_form_url = None
    newsletter_email = os.getenv("NEWSLETTER_EMAIL", "").strip() or None
    env_file = root_dir / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("NEWSLETTER_FORM_URL="):
                newsletter_form_url = line.split("=", 1)[1].strip()
            if line.startswith("NEWSLETTER_EMAIL="):
                newsletter_email = line.split("=", 1)[1].strip() or None

    for topic in topics:
        slug = slugify(topic.title)
        if state.has_slug(slug):
            continue
        tags = (topic.keywords[:5] or ["seo", "contenido", "trafico"])
        categories = ["blog", "seo"]
        canonical = f"{site_url}/posts/{slug}/"

        article = generate_article(
            topic=topic.title,
            slug=slug,
            date_str=datetime.now(timezone.utc).date().isoformat(),
            tags=tags,
            categories=categories,
            canonical=canonical,
        )
        quality = article["quality"]
        if not quality.ok:
            logger.warning("quality_gate failed for %s: %s", slug, quality.reasons)
            continue

        related = _related_links(tags, existing)
        interlinks = ["## Lecturas relacionadas", ""]
        for item in related:
            related_path = Path(item.get("path", "")).name
            interlinks.append(f"- [{item.get('title', 'Articulo relacionado')}]({related_path})")
        interlinks.append(f"- [{pillar['title']}](../{pillar['path']})")

        products, disclaimer = select_affiliate_items(affiliates_cfg, tags, categories)
        monetization_block = recommendations_markdown(products, disclaimer)

        markdown = (
            _frontmatter_to_yaml(article["frontmatter"])
            + "\n\n"
            + article["body"]
            + "\n\n"
            + "\n".join(interlinks)
            + "\n\n"
            + monetization_block
            + "\n\n"
            + _newsletter_block(newsletter_form_url, newsletter_email)
            + "\n\n"
            + _lead_magnet_block()
            + "\n\n"
            + article["json_ld"]
        )

        post_path = posts_dir / f"{slug}.md"
        if not dry_run:
            post_path.write_text(markdown, encoding="utf-8")

        snippets = make_social_snippets(article["frontmatter"]["title"], canonical, tags)
        social_dir = root_dir / "outputs" / "social" / slug
        if not dry_run:
            social_dir.mkdir(parents=True, exist_ok=True)
            (social_dir / "twitter.txt").write_text(snippets["twitter"], encoding="utf-8")
            (social_dir / "linkedin.txt").write_text(snippets["linkedin"], encoding="utf-8")
            (social_dir / "reddit.txt").write_text(snippets["reddit"], encoding="utf-8")

        record = StateRecord(
            slug=slug,
            title=article["frontmatter"]["title"],
            date=article["frontmatter"]["date"],
            path=f"posts/{slug}.md",
            tags=tags,
            categories=categories,
        )
        if not dry_run:
            state.add_post(record)

        entry = {
            "title": article["frontmatter"]["title"],
            "path": f"posts/{slug}/",
            "date": article["frontmatter"]["date"],
            "description": article["frontmatter"]["description"],
        }
        created.append(entry)
        existing.append({"title": entry["title"], "path": f"posts/{slug}.md", "tags": tags})

        if len(created) >= limit:
            break

    if not dry_run:
        (root_dir / "outputs").mkdir(parents=True, exist_ok=True)
        (root_dir / "outputs" / "last_generated.json").write_text(
            json.dumps(created, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return created


def build_site_assets(root_dir: Path, dry_run: bool = False) -> dict[str, int]:
    config_loader = ConfigLoader(root_dir)
    site_cfg = config_loader.load_site()
    site_url = resolved_site_url(site_cfg.site_url, root_dir.name)
    docs_dir = root_dir / "docs"

    entries = _load_existing_posts(docs_dir)
    normalized_entries = []
    for item in entries:
        path = item.get("path", "")
        if path.endswith(".md"):
            path = path[:-3] + "/"
        normalized_entries.append(
            {
                "title": item.get("title", "Post"),
                "path": path,
                "date": item.get("date", datetime.now(timezone.utc).date().isoformat()),
                "description": item.get("description", ""),
            }
        )

    write_text(docs_dir / "assets" / "robots.txt", build_robots(site_url), dry_run)
    write_text(docs_dir / "sitemap.xml", build_sitemap(site_url, normalized_entries), dry_run)
    write_text(docs_dir / "rss.xml", build_rss(site_url, site_cfg.site_name, normalized_entries), dry_run)

    lead_magnet_path = docs_dir / "assets" / "lead-magnet.md"
    if not dry_run and not lead_magnet_path.exists():
        lead_magnet_path.write_text(
            "# Plantilla gratis\n\nUsa esta plantilla semanal para planificar contenidos SEO y tareas de distribucion.",
            encoding="utf-8",
        )

    return {"entries": len(normalized_entries)}
