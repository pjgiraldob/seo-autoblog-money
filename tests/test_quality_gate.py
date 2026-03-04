from seo_factory.content_generator import quality_gate


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
