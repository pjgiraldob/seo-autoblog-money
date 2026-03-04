from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class QualityGateResult:
    ok: bool
    reasons: list[str]


def _word_count(text: str) -> int:
    return len([w for w in text.split() if w.strip()])


def _h2_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("## "))


def _faq_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("### "))


def _english_ratio(text: str) -> float:
    english_markers = {
        "the", "and", "for", "with", "best", "top", "tools", "workflow", "how", "to", "guide", "work",
        "developers", "business", "productivity", "content", "creation", "startup", "repetitive", "using",
    }
    tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())
    if not tokens:
        return 0.0
    hits = sum(1 for t in tokens if t in english_markers)
    return hits / len(tokens)


def _spanish_ratio(text: str) -> float:
    spanish_markers = {
        "que", "para", "con", "guia", "como", "herramientas", "flujo", "trabajo", "negocio", "productividad",
        "desarrolladores", "automatizacion", "contenido", "crear", "usar", "mejor", "pasos", "seccion",
    }
    tokens = re.findall(r"[a-zA-Záéíóúñ]{3,}", text.lower())
    if not tokens:
        return 0.0
    hits = sum(1 for t in tokens if t in spanish_markers)
    return hits / len(tokens)


def _is_language_consistent(text: str, language: str) -> bool:
    lang = (language or "es").lower()
    if lang.startswith("es"):
        return _english_ratio(text) <= 0.08
    if lang.startswith("en"):
        return _spanish_ratio(text) <= 0.08
    return True


def quality_gate(meta_description: str, body: str, language: str = "es") -> QualityGateResult:
    reasons: list[str] = []
    desc_len = len(meta_description.strip())
    if not (120 <= desc_len <= 160):
        reasons.append("meta_description fuera de rango (120-160)")

    wc = _word_count(body)
    if wc < 1200 or wc > 1800:
        reasons.append("longitud fuera de rango (1200-1800)")

    if _h2_count(body) < 5:
        reasons.append("faltan H2 (minimo 5)")

    if _faq_count(body) < 5:
        reasons.append("faltan FAQs (minimo 5)")

    if not _is_language_consistent(f"{meta_description}\n{body}", language):
        reasons.append(f"idioma mezclado: se esperaba contenido consistente en '{language}'")

    return QualityGateResult(ok=not reasons, reasons=reasons)


def _localize_topic(topic: str, language: str = "es") -> str:
    lang = (language or "es").lower()
    if not lang.startswith("es"):
        return topic.strip()

    text = topic.strip()
    replacements = [
        ("Best ", "Mejores "),
        ("Top ", "Principales "),
        ("How to ", "Como "),
        ("powered by", "impulsadas por"),
        ("for developers", "para desarrolladores"),
        ("for startups", "para startups"),
        ("for content creation", "para creacion de contenido"),
        ("for business workflows", "para flujos de trabajo de negocio"),
        ("workflow automation", "automatizacion de flujos de trabajo"),
        ("automation tools", "herramientas de automatizacion"),
        ("productivity tools", "herramientas de productividad"),
        ("no-code", "sin codigo"),
        ("save time at work", "ahorran tiempo en el trabajo"),
        ("repetitive work", "trabajo repetitivo"),
        ("using AI", "usando IA"),
        ("AI tools", "herramientas de IA"),
        ("AI", "IA"),
    ]
    for source, target in replacements:
        text = re.sub(re.escape(source), target, text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text).strip()
    return text


def _make_intro(topic: str) -> str:
    return (
        f"{topic} es una oportunidad real para captar trafico organico con intencion de busqueda clara. "
        "En esta guia te muestro un proceso completo para investigar, priorizar y publicar sin depender de herramientas pagas.\n\n"
        "La idea central es simple: combinar SEO tecnico, contenido util y medicion basica para iterar cada semana. "
        "Si aplicas este flujo con consistencia, puedes crecer en visibilidad de forma sostenible.\n\n"
        "Tambien veremos como enlazar internamente, donde colocar llamadas a la accion y como preparar activos "
        "que ayuden tanto al lector como al rendimiento del sitio."
    )


def _section(topic: str, n: int) -> str:
    section_titles = [
        "Investigacion y enfoque",
        "Arquitectura de contenido",
        "Implementacion operativa",
        "Distribucion y amplificacion",
        "Medicion y optimizacion",
        "Escalado sostenible",
    ]
    title = section_titles[(n - 1) % len(section_titles)]
    return (
        f"## Estrategia {n}: {title} en {topic.lower()}\n\n"
        f"### Diagnostico {n}.1\n"
        "Empieza con una hipotesis clara: que problema resuelves, para quien y con que promesa de resultado. "
        "Con esa base, puedes descartar ideas atractivas pero poco rentables y concentrarte en oportunidades que "
        "realmente muevan negocio.\n\n"
        f"### Ejecucion {n}.2\n"
        "Define una secuencia de acciones simple: investigacion, produccion, revision y publicacion. "
        "Cada etapa debe tener un criterio de salida concreto para evitar retrabajo y asegurar consistencia editorial. "
        "Cuando el proceso es predecible, el equipo reduce friccion y publica con mejor calidad.\n\n"
        f"### Control {n}.3\n"
        "Asocia cada bloque a una metrica accionable: clics organicos, tiempo en pagina, profundidad de scroll o "
        "conversion en CTA. No hace falta medir todo; basta con dos o tres indicadores por articulo para detectar "
        "que secciones ayudan y cuales deben reescribirse."
    )


def _checklist_table() -> str:
    return (
        "## Checklist operativo\n\n"
        "| Tarea | Frecuencia | Objetivo |\n"
        "|---|---|---|\n"
        "| Revisar query principal | Semanal | Mantener foco tematico |\n"
        "| Mejorar encabezados H2/H3 | Quincenal | Aumentar escaneo del contenido |\n"
        "| Actualizar interlinking | Semanal | Repartir autoridad interna |\n"
        "| Medir clics en CTA | Semanal | Mejorar conversion de lead magnet |\n"
    )


def _faq_block(topic: str) -> str:
    faqs = [
        (f"Que es lo primero que debo hacer para trabajar {topic.lower()}?", "Define una keyword objetivo y una promesa concreta para el lector."),
        ("Cuanto tarda en notarse una mejora SEO?", "Normalmente entre 4 y 12 semanas, dependiendo del nicho y la competencia."),
        ("Cuantos enlaces internos deberia incluir?", "Como base, incluye al menos tres: dos relacionados y uno pilar."),
        ("Necesito publicar todos los dias?", "No. Es mejor mantener una frecuencia sostenible con calidad consistente."),
        ("Como mido si el articulo funciona?", "Evalua posicionamiento, clics organicos, tiempo de lectura y conversion en CTA."),
    ]
    lines = ["## FAQ"]
    for question, answer in faqs:
        lines.append("")
        lines.append(f"### {question}")
        lines.append(answer)
    return "\n".join(lines)


def _expansion_blocks(topic: str) -> list[str]:
    return [
        (
            "## Errores comunes y como evitarlos\n\n"
            f"Uno de los errores mas frecuentes al trabajar {topic.lower()} es publicar sin una tesis clara. "
            "Eso genera piezas largas pero debiles, sin foco y con baja conversion. Define primero una promesa "
            "especifica para el lector y valida que cada seccion contribuya a esa promesa.\n\n"
            "Otro error es depender solo de intuicion. Usa datos minimos: consultas que activan impresiones, "
            "secciones con mayor permanencia y enlaces internos con mejor CTR. Esa informacion evita decisiones "
            "aleatorias y acelera mejoras de forma consistente."
        ),
        (
            "## Plan de 30 dias para implementarlo\n\n"
            "Semana 1: define temas prioritarios y crea un esquema por articulo con objetivos medibles.\n\n"
            "Semana 2: publica, enlaza internamente y revisa legibilidad en desktop y mobile.\n\n"
            "Semana 3: optimiza titulares, FAQs y bloques de recomendacion segun datos de comportamiento.\n\n"
            "Semana 4: compara resultados, documenta aprendizajes y estandariza el flujo para el siguiente ciclo.\n\n"
            "Este ritmo mensual evita saturacion y te permite mejorar sin romper la operacion diaria."
        ),
    ]


def _build_jsonld(title: str, description: str, canonical: str, faqs: list[tuple[str, str]]) -> str:
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "mainEntityOfPage": canonical,
        "datePublished": datetime.utcnow().date().isoformat(),
    }
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }

    return (
        "<script type=\"application/ld+json\">"
        + json.dumps(article, ensure_ascii=False)
        + "</script>\n"
        + "<script type=\"application/ld+json\">"
        + json.dumps(faq_schema, ensure_ascii=False)
        + "</script>"
    )


def generate_article(
    topic: str,
    slug: str,
    date_str: str,
    tags: list[str],
    categories: list[str],
    canonical: str,
    language: str = "es",
) -> dict[str, Any]:
    title = _localize_topic(topic.strip(), language=language)
    meta_description = (
        f"Guia practica para {title.lower()} con pasos accionables, SEO tecnico, interlinking y monetizacion por afiliados sin costo inicial."
    )
    if len(meta_description) < 120:
        meta_description += " Incluye checklist, FAQ y recursos para ejecutar hoy mismo."
    meta_description = meta_description[:160].strip()

    sections = [_section(topic, i) for i in range(1, 7)]
    body_parts = [
        f"# {title}",
        "",
        _make_intro(topic),
        "",
        *sections,
        "",
        *_expansion_blocks(topic),
        "",
        _checklist_table(),
        "",
        _faq_block(topic),
        "",
        "## Conclusión",
        "Aplica este marco durante cuatro semanas, registra resultados y optimiza en ciclos cortos. "
        "La mejora sostenida llega cuando conviertes cada publicacion en un activo reutilizable.",
    ]

    body = "\n".join(body_parts)

    if _word_count(body) < 1200:
        body += (
            "\n\n## Nota de implementacion\n"
            "Si el articulo queda corto, prioriza ampliar ejemplos reales, casos de uso y decisiones tacticas. "
            "Evita repetir texto literal; cada parrafo adicional debe aportar una accion concreta o una evidencia nueva."
        )

    faq_pairs = [
        ("Que es lo primero que debo hacer para empezar?", "Define la intencion principal y un objetivo medible por URL."),
        ("Debo cambiar todo el contenido viejo?", "No, empieza por las paginas con mas potencial de mejora."),
        ("Cuantos enlaces internos usar?", "Como base, tres enlaces contextuales bien alineados al tema."),
        ("Puedo monetizar sin trafico masivo?", "Si, siempre que alinees oferta con problema concreto."),
        ("Cada cuanto actualizar este articulo?", "Revisalo al menos una vez al mes con datos reales."),
    ]
    json_ld = _build_jsonld(title, meta_description, canonical, faq_pairs)

    frontmatter = {
        "title": title,
        "slug": slug,
        "date": date_str,
        "description": meta_description,
        "tags": tags,
        "categories": categories,
        "canonical": canonical,
    }

    gate = quality_gate(meta_description, body, language=language)
    if not gate.ok:
        body = body.replace("## Conclusion", "## Conclusión")
        body = _localize_topic(body, language=language)
        body += "\n\n## Anexo\nResumen de buenas practicas y puntos de control para ejecucion continua."
        gate = quality_gate(meta_description, body, language=language)

    return {
        "frontmatter": frontmatter,
        "body": body,
        "json_ld": json_ld,
        "quality": gate,
    }
