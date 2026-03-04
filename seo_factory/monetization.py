from __future__ import annotations

from typing import Any


def select_affiliate_items(
    affiliates_cfg: dict[str, Any],
    tags: list[str],
    categories: list[str],
    max_items: int = 3,
) -> tuple[list[dict[str, str]], str]:
    by_keyword = affiliates_cfg.get("by_keyword", {})
    by_category = affiliates_cfg.get("by_category", {})
    disclaimer = affiliates_cfg.get(
        "default_disclaimer",
        "Enlaces afiliados: puedo recibir comision sin costo extra para ti.",
    )

    selected: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for tag in tags:
        for item in by_keyword.get(tag.lower(), []):
            url = item.get("url", "")
            if url and url not in seen_urls:
                selected.append(item)
                seen_urls.add(url)
            if len(selected) >= max_items:
                return selected, disclaimer

    for category in categories:
        for item in by_category.get(category.lower(), []):
            url = item.get("url", "")
            if url and url not in seen_urls:
                selected.append(item)
                seen_urls.add(url)
            if len(selected) >= max_items:
                return selected, disclaimer

    for item in affiliates_cfg.get("fallback", []):
        url = item.get("url", "")
        if url and url not in seen_urls:
            selected.append(item)
            seen_urls.add(url)
        if len(selected) >= max_items:
            break

    return selected, disclaimer


def recommendations_markdown(items: list[dict[str, str]], disclaimer: str) -> str:
    lines = ["## Recomendaciones", ""]
    if not items:
        lines.append("Aun no hay recomendaciones especificas para este tema.")
    else:
        for item in items:
            name = item.get("name", "Recurso recomendado")
            url = item.get("url", "#")
            note = item.get("disclaimer", "")
            lines.append(f"- [{name}]({url})")
            if note:
                lines.append(f"  - {note}")
    lines.append("")
    lines.append(f"**{disclaimer}**")
    return "\n".join(lines)
