from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .config import ConfigLoader
from .logging_setup import setup_logging
from .site_builder import build_site_assets, generate_posts
from .topic_discovery import discover_topics

logger = logging.getLogger(__name__)


def _root_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def cmd_discover(args: argparse.Namespace) -> int:
    root = _root_dir()
    setup_logging(root / "logs")
    config_loader = ConfigLoader(root)
    sources_cfg = config_loader.load_sources()
    topics = discover_topics(sources_cfg, args.limit)

    payload = [
        {
            "title": t.title,
            "source": t.source,
            "keywords": t.keywords,
            "score": t.score,
            "published_at": t.published_at,
        }
        for t in topics
    ]

    if not args.dry_run:
        out = root / "outputs" / "discovered_topics.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    root = _root_dir()
    setup_logging(root / "logs")
    created = generate_posts(root, limit=args.limit, dry_run=args.dry_run)
    logger.info("Generated %s posts", len(created))
    print(json.dumps(created, ensure_ascii=False, indent=2))
    return 0


def cmd_build_site(args: argparse.Namespace) -> int:
    root = _root_dir()
    setup_logging(root / "logs")
    result = build_site_assets(root, dry_run=args.dry_run)
    logger.info("Built SEO assets for %s entries", result["entries"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    root = _root_dir()
    setup_logging(root / "logs")
    created = generate_posts(root, limit=args.limit, dry_run=args.dry_run)
    result = build_site_assets(root, dry_run=args.dry_run)
    logger.info("Run complete | posts=%s assets_entries=%s", len(created), result["entries"])
    print(json.dumps({"generated": len(created), **result}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m seo_factory")
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover", help="Discover topics from configured sources")
    discover.add_argument("--limit", type=int, default=20)
    discover.add_argument("--dry-run", action="store_true")
    discover.set_defaults(func=cmd_discover)

    generate = sub.add_parser("generate", help="Generate SEO posts")
    generate.add_argument("--limit", type=int, default=3)
    generate.add_argument("--dry-run", action="store_true")
    generate.set_defaults(func=cmd_generate)

    build_site = sub.add_parser("build-site", help="Generate technical SEO assets")
    build_site.add_argument("--dry-run", action="store_true")
    build_site.set_defaults(func=cmd_build_site)

    run = sub.add_parser("run", help="Run discover->generate->build-site pipeline")
    run.add_argument("--daily", action="store_true", help="Compatibility flag for scheduled runs")
    run.add_argument("--limit", type=int, default=3)
    run.add_argument("--dry-run", action="store_true")
    run.set_defaults(func=cmd_run)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
