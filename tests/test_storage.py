from seo_factory.storage import normalize_text, slugify


def test_normalize_text_removes_accents_and_symbols():
    assert normalize_text("SEO Tecnico: Guia Rapida!!!") == "seo tecnico guia rapida"


def test_slugify_basic():
    assert slugify("Hola Mundo SEO") == "hola-mundo-seo"


def test_slugify_empty_fallback():
    assert slugify("!!!") == "post"
