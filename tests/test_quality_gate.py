from seo_factory.content_generator import _localize_topic, quality_gate


def test_quality_gate_passes_valid_content():
    meta = "Guia completa para posicionar contenido de forma organica con pasos claros, SEO tecnico y conversion sostenible en tu sitio web hoy."
    body = "\n".join(
        [
            "# Titulo",
            "## H2 1",
            "### Q1",
            "a " * 250,
            "## H2 2",
            "### Q2",
            "a " * 250,
            "## H2 3",
            "### Q3",
            "a " * 250,
            "## H2 4",
            "### Q4",
            "a " * 250,
            "## H2 5",
            "### Q5",
            "a " * 250,
        ]
    )
    result = quality_gate(meta, body)
    assert result.ok


def test_quality_gate_fails_invalid_content():
    result = quality_gate("corto", "# Titulo\n## H2\n### Q\ntexto")
    assert not result.ok
    assert len(result.reasons) >= 1


def test_quality_gate_detects_mixed_language_when_es():
    meta = "Guia practica para automatizacion y productividad con pasos accionables para equipos tecnicos."
    body = "\n".join(
        [
            "# Best AI tools for developers",
            "## H2 1",
            "### Q1",
            "the best tools for workflow automation and business teams " * 60,
            "## H2 2",
            "### Q2",
            "the best tools for workflow automation and business teams " * 60,
            "## H2 3",
            "### Q3",
            "the best tools for workflow automation and business teams " * 60,
            "## H2 4",
            "### Q4",
            "the best tools for workflow automation and business teams " * 60,
            "## H2 5",
            "### Q5",
            "the best tools for workflow automation and business teams " * 60,
        ]
    )
    result = quality_gate(meta, body, language="es")
    assert not result.ok
    assert any("idioma mezclado" in r for r in result.reasons)


def test_localize_topic_to_spanish():
    topic = "Best AI automation tools for developers"
    localized = _localize_topic(topic, language="es")
    assert "Mejores" in localized
    assert "IA" in localized
    assert "desarrolladores" in localized
