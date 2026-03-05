from __future__ import annotations

import json
import re
import zlib
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
        return _english_ratio(text) <= 0.18
    if lang.startswith("en"):
        return _spanish_ratio(text) <= 0.18
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
        ("best tools to automate business workflows", "mejores herramientas para automatizar flujos de negocio"),
        ("best ai automation tools for developers", "mejores herramientas de automatizacion con IA para desarrolladores"),
        ("best productivity tools powered by ai", "mejores herramientas de productividad impulsadas por IA"),
        ("top workflow automation tools in 2026", "principales herramientas de automatizacion de flujos en 2026"),
        ("ai tools that save time at work", "herramientas de IA que ahorran tiempo en el trabajo"),
        ("top no-code automation platforms", "principales plataformas de automatizacion sin codigo"),
        ("best ai tools for content creation", "mejores herramientas de IA para creacion de contenido"),
        ("best ai tools for developers", "mejores herramientas de IA para desarrolladores"),
        ("best ai tools for startups", "mejores herramientas de IA para startups"),
        ("how to automate repetitive work using ai", "como automatizar trabajo repetitivo usando IA"),
        ("Best ", "Mejores "),
        ("Top ", "Principales "),
        ("How to ", "Como "),
        ("powered by", "impulsadas por"),
        ("business workflows", "flujos de negocio"),
        ("automation platforms", "plataformas de automatizacion"),
        ("automation", "automatizacion"),
        ("tools", "herramientas"),
        ("to automate", "para automatizar"),
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
    if text:
        text = text[0].upper() + text[1:]
    return text


def _topic_profile(topic: str, slug: str) -> str:
    text = f"{topic} {slug}".lower()
    if "developer" in text or "desarrollador" in text:
        return "developers"
    if "productivity" in text or "productividad" in text:
        return "productivity"
    if "no-code" in text or "sin-codigo" in text or "sin codigo" in text:
        return "nocode"
    if "startup" in text:
        return "startup"
    if "content" in text or "contenido" in text:
        return "content"
    if "workflow" in text or "flujos" in text:
        return "workflow"
    if "business" in text or "negocio" in text:
        return "business"
    if "time" in text or "tiempo" in text:
        return "timesaving"
    if "repetitive" in text or "repetitivo" in text:
        return "howto"
    return "general"


def _make_intro(topic: str, profile: str) -> str:
    openers = {
        "developers": "Para equipos de desarrollo, automatizar tareas repetitivas libera horas de foco tecnico y reduce retrabajo en sprint.",
        "productivity": "En entornos con alta carga operativa, la productividad mejora cuando combinas procesos simples con asistentes de IA bien definidos.",
        "workflow": "Los flujos de trabajo modernos exigen menos pasos manuales y mas integracion entre herramientas.",
        "business": "En operaciones de negocio, la automatizacion rentable es la que reduce costos sin perder control del proceso.",
        "timesaving": "Si el objetivo es recuperar tiempo, conviene empezar por tareas frecuentes y de baja complejidad.",
        "nocode": "Las plataformas sin codigo permiten que equipos no tecnicos automaticen procesos sin depender siempre de desarrollo.",
        "content": "La creacion de contenido escala mejor cuando combinas IA para borradores con criterio editorial humano.",
        "startup": "En startups, la velocidad de ejecucion depende de tener sistemas ligeros y repetibles.",
        "howto": "Para automatizar trabajo repetitivo de forma segura, necesitas una secuencia practica y medible.",
        "general": "La automatizacion bien aplicada convierte tareas operativas en sistemas repetibles y predecibles.",
    }
    return (
        f"{openers.get(profile, openers['general'])} "
        f"{topic} es una oportunidad real para captar trafico organico con intencion de busqueda clara. "
        "En esta guia te muestro un proceso completo para investigar, priorizar y publicar sin depender de herramientas pagas.\n\n"
        "La idea central es simple: combinar SEO tecnico, contenido util y medicion basica para iterar cada semana. "
        "Si aplicas este flujo con consistencia, puedes crecer en visibilidad de forma sostenible.\n\n"
        "Tambien veremos como enlazar internamente, donde colocar llamadas a la accion y como preparar activos "
        "que ayuden tanto al lector como al rendimiento del sitio."
    )


def _section_banks(profile: str) -> list[tuple[str, str, list[str]]]:
    common = [
        ("Criterio de seleccion", "Define criterios de comparacion antes de elegir herramientas: costo total, curva de adopcion y capacidad de integracion.", ["Documenta criterios", "Asigna peso por criterio", "Descarta opciones sin integracion"]),
        ("Implementacion inicial", "Empieza con un piloto reducido de 7 a 14 dias para validar adopcion real y estabilidad.", ["Elige un proceso", "Mide antes/despues", "Evalua friccion operativa"]),
        ("Riesgos y control", "Todo sistema automatizado requiere reglas de control, monitoreo de errores y responsable de mantenimiento.", ["Define alertas", "Crea plan de rollback", "Revisa errores semanalmente"]),
        ("Indicadores de impacto", "No midas solo volumen. Mide tiempo ahorrado, calidad del resultado y mejora de conversion.", ["Define 3 KPI", "Compara por cohorte", "Ajusta cada 2 semanas"]),
        ("Escala sin caos", "Escala solo lo que ya funciona en pequeño. Estandariza antes de multiplicar.", ["Plantillas de proceso", "Checklist de QA", "Bitacora de cambios"]),
        ("Roadmap de mejora", "La ventaja competitiva aparece cuando conviertes optimizaciones en un ciclo continuo.", ["Prioriza mejoras", "Ejecuta iteraciones cortas", "Publica aprendizajes internos"]),
    ]
    by_profile = {
        "developers": [
            ("Automatizacion en desarrollo", "Prioriza tareas de alto volumen: tests repetitivos, revisiones de estilo, generacion de docs y scaffolding.", ["Mapea tareas repetitivas", "Automatiza en CI", "Mide tiempo por pull request"]),
            ("Integracion con repositorio", "El valor real llega cuando la herramienta vive en el flujo del equipo y no como app aislada.", ["Configura hooks", "Conecta issue tracker", "Define convenciones de commit"]),
        ],
        "productivity": [
            ("Sistema de foco diario", "La productividad mejora cuando automatizas contexto: prioridades, calendario y recordatorios de seguimiento.", ["Bloques de trabajo profundo", "Reglas de notificacion", "Reunion de cierre semanal"]),
            ("Evitar sobreautomatizacion", "No todo se debe automatizar; protege tareas creativas y decisiones de alto contexto.", ["Lista de excepciones", "Revision quincenal", "Reglas de override manual"]),
        ],
        "workflow": [
            ("Mapa de flujo extremo a extremo", "Antes de elegir herramienta, visualiza dependencias entre equipos, aprobaciones y handoffs.", ["Diagrama actual", "Cuellos de botella", "Version objetivo"]),
            ("Orquestacion entre sistemas", "La automatizacion falla cuando cada app trabaja aislada. Diseña eventos y estados comunes.", ["Evento de inicio/fin", "Estados unificados", "Validacion de datos"]),
        ],
        "business": [
            ("Impacto en margen", "Automatizar sin vincular costo y margen produce actividad, no resultados.", ["Costo por proceso", "Tiempo por tarea", "Impacto en margen bruto"]),
            ("Automatizacion comercial", "En ventas y ops, automatiza seguimiento, scoring y pasos de onboarding.", ["Lead scoring", "Secuencias de seguimiento", "Alertas de riesgo"]),
        ],
        "timesaving": [
            ("Auditoria de tiempo real", "Empieza por actividades recurrentes de bajo valor y alto consumo horario.", ["Top 10 tareas", "Minutos por tarea", "Frecuencia semanal"]),
            ("Recuperar horas utiles", "El objetivo no es automatizar por moda, sino liberar tiempo para trabajo estrategico.", ["Horas recuperadas", "Reasignacion de tiempo", "Resultado semanal"]),
        ],
        "nocode": [
            ("Seleccion de plataforma no-code", "Compara limites de ejecucion, conectores, costos por volumen y trazabilidad.", ["Limites tecnicos", "Estructura de costos", "Disponibilidad de integraciones"]),
            ("Gobierno de flujos", "Sin governance, los escenarios no-code se rompen al crecer el equipo.", ["Control de versiones", "Permisos por rol", "Responsable por flujo"]),
        ],
        "content": [
            ("Pipeline editorial con IA", "La IA acelera borradores, pero la calidad final depende de criterio editorial humano.", ["Brief por pieza", "Reglas de estilo", "Validacion de hechos"]),
            ("Distribucion multicanal", "Un articulo rinde mas cuando se adapta por canal sin perder tesis central.", ["Version newsletter", "Resumen social", "Enlaces internos tematicos"]),
        ],
        "startup": [
            ("Stack minimo viable", "En startups, gana la simplicidad: pocas herramientas bien conectadas superan stacks complejos.", ["3 herramientas maximo", "Integracion clave", "Costo mensual controlado"]),
            ("Ejecucion con equipo pequeno", "Automatiza tareas administrativas para proteger tiempo de producto y ventas.", ["Rutinas operativas", "Dashboard unico", "Revision semanal corta"]),
        ],
        "howto": [
            ("Metodo paso a paso", "Empieza por un flujo unico, define objetivo, ejecuta piloto y escala con evidencia.", ["Objetivo del piloto", "Ejecucion guiada", "Criterio de exito"]),
            ("Errores frecuentes al iniciar", "Los primeros fallos suelen venir por falta de datos, pasos ambiguos y ausencia de responsable.", ["Datos de entrada", "Secuencia clara", "Dueño del proceso"]),
        ],
    }
    return by_profile.get(profile, []) + common


def _build_sections(topic: str, slug: str, profile: str) -> list[str]:
    bank = _section_banks(profile)
    if len(bank) < 6:
        return []
    start = zlib.crc32(slug.encode("utf-8")) % len(bank)
    sections: list[str] = []
    for idx in range(6):
        title, paragraph, actions = bank[(start + idx) % len(bank)]
        sections.append(
            f"## Bloque {idx + 1}: {title}\n\n"
            f"{paragraph}\n\n"
            f"Aplicado a {topic.lower()}, este bloque ayuda a pasar de ideas generales a ejecucion concreta.\n\n"
            "Checklist de ejecucion:\n"
            f"- {actions[0]}\n"
            f"- {actions[1]}\n"
            f"- {actions[2]}"
        )
    return sections


def _checklist_table(profile: str) -> str:
    profile_row = {
        "developers": "| Revisar tiempo de ciclo dev | Semanal | Reducir bloqueos en entrega |\n",
        "productivity": "| Medir tareas completadas | Semanal | Mejorar foco y ejecucion |\n",
        "workflow": "| Auditar tiempos por etapa | Semanal | Detectar cuellos de botella |\n",
        "business": "| Revisar costo por proceso | Quincenal | Mejorar margen operativo |\n",
        "timesaving": "| Medir horas recuperadas | Semanal | Ganar capacidad de ejecucion |\n",
        "nocode": "| Validar flujos sin error | Semanal | Garantizar continuidad |\n",
        "content": "| Revisar calidad editorial | Semanal | Mantener consistencia de marca |\n",
        "startup": "| Medir impacto por automatizacion | Semanal | Priorizar crecimiento |\n",
        "howto": "| Verificar adopcion del proceso | Semanal | Evitar recaida manual |\n",
    }
    return (
        "## Checklist operativo\n\n"
        "| Tarea | Frecuencia | Objetivo |\n"
        "|---|---|---|\n"
        "| Revisar query principal | Semanal | Mantener foco tematico |\n"
        "| Mejorar encabezados H2/H3 | Quincenal | Aumentar escaneo del contenido |\n"
        "| Actualizar interlinking | Semanal | Repartir autoridad interna |\n"
        "| Medir clics en CTA | Semanal | Mejorar conversion de lead magnet |\n"
        + profile_row.get(profile, "")
    )


def _faq_block(topic: str, profile: str) -> str:
    profile_q = {
        "developers": "Que herramienta de IA integra mejor con repos y CI?",
        "productivity": "Como priorizo que automatizar primero en mi semana?",
        "workflow": "Como elijo el mejor flujo para mi operacion actual?",
        "business": "Como justifico ROI de automatizacion ante direccion?",
        "timesaving": "Que tareas conviene automatizar para ahorrar tiempo real?",
        "nocode": "Hasta donde escalan las plataformas sin codigo?",
        "content": "Como evitar contenido generico al usar IA?",
        "startup": "Que automatizaciones dan mas impacto con poco presupuesto?",
        "howto": "Como empiezo sin romper procesos actuales?",
    }
    faqs = [
        (profile_q.get(profile, f"Que es lo primero que debo hacer para trabajar {topic.lower()}?"), "Define una keyword objetivo y una promesa concreta para el lector."),
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


def _expansion_blocks(topic: str, profile: str) -> list[str]:
    profile_hint = {
        "developers": "Incluye pruebas de regresion y control de calidad de codigo en cada iteracion.",
        "productivity": "Evita automatizar tareas que requieren criterio humano alto en fases tempranas.",
        "workflow": "Documenta handoffs entre equipos para evitar quiebres del proceso.",
        "business": "Asocia cada automatizacion a un indicador de costo o ingreso.",
        "timesaving": "Prioriza tareas de alta frecuencia y bajo valor estrategico.",
        "nocode": "Define responsables para mantenimiento de escenarios y permisos.",
        "content": "Combina borrador asistido con edicion humana para mantener voz de marca.",
        "startup": "Empieza con soluciones reversibles y de baja complejidad.",
        "howto": "Pilota en un solo proceso antes de escalar al resto de la organizacion.",
    }
    return [
        (
            "## Errores comunes y como evitarlos\n\n"
            f"Uno de los errores mas frecuentes al trabajar {topic.lower()} es publicar sin una tesis clara. "
            "Eso genera piezas largas pero debiles, sin foco y con baja conversion. Define primero una promesa "
            "especifica para el lector y valida que cada seccion contribuya a esa promesa.\n\n"
            "Otro error es depender solo de intuicion. Usa datos minimos: consultas que activan impresiones, "
            "secciones con mayor permanencia y enlaces internos con mejor CTR. Esa informacion evita decisiones "
            "aleatorias y acelera mejoras de forma consistente. "
            + profile_hint.get(profile, "")
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
    profile = _topic_profile(topic, slug)
    title = _localize_topic(topic.strip(), language=language)
    meta_description = (
        f"Guia practica para {title.lower()} con pasos accionables, SEO tecnico, interlinking y monetizacion por afiliados sin costo inicial."
    )
    if len(meta_description) < 120:
        meta_description += " Incluye checklist, FAQ y recursos para ejecutar hoy mismo."
    meta_description = meta_description[:160].strip()

    sections = _build_sections(title, slug, profile=profile)
    body_parts = [
        f"# {title}",
        "",
        _make_intro(title, profile=profile),
        "",
        *sections,
        "",
        *_expansion_blocks(topic, profile=profile),
        "",
        _checklist_table(profile=profile),
        "",
        _faq_block(topic, profile=profile),
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
        body += "\n\n## Anexo\nResumen de buenas practicas y puntos de control para ejecucion continua."
        gate = quality_gate(meta_description, body, language=language)

    return {
        "frontmatter": frontmatter,
        "body": body,
        "json_ld": json_ld,
        "quality": gate,
    }
