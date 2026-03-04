from __future__ import annotations


def make_social_snippets(title: str, url: str, tags: list[str]) -> dict[str, str]:
    hashtag_line = " ".join(f"#{t.replace('-', '')}" for t in tags[:3])
    twitter = (
        f"Nuevo articulo: {title}.\n"
        f"Ideas aplicables para mejorar SEO hoy mismo.\n"
        f"{url}\n"
        f"{hashtag_line}"
    )
    twitter = twitter[:280]

    linkedin = (
        f"Acabo de publicar una guia practica: {title}.\n\n"
        "Incluye pasos, checklist, errores comunes y FAQ para aplicar SEO tecnico y contenido de forma medible.\n"
        f"Lectura completa: {url}\n"
        "Si estas construyendo trafico organico sostenible, te puede ahorrar tiempo."
    )

    reddit = (
        f"Comparto un recurso sobre {title.lower()}. "
        "Evite relleno y me enfoque en un proceso accionable con secciones tecnicas y ejemplos. "
        f"Feedback bienvenido: {url}"
    )

    return {"twitter": twitter, "linkedin": linkedin, "reddit": reddit}
