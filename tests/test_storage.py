from seo_factory.storage import StateRecord, StateStore, normalize_text, slugify


def test_normalize_text_removes_accents_and_symbols():
    assert normalize_text("SEO Tecnico: Guia Rapida!!!") == "seo tecnico guia rapida"


def test_slugify_basic():
    assert slugify("Hola Mundo SEO") == "hola-mundo-seo"


def test_slugify_empty_fallback():
    assert slugify("!!!") == "post"


def test_state_count_posts_on_date(tmp_path):
    state = StateStore(tmp_path / "state.json")
    state.add_post(
        StateRecord(
            slug="uno",
            title="Uno",
            date="2026-03-04",
            path="posts/uno.md",
            tags=["a"],
            categories=["blog"],
        )
    )
    state.add_post(
        StateRecord(
            slug="dos",
            title="Dos",
            date="2026-03-05",
            path="posts/dos.md",
            tags=["b"],
            categories=["blog"],
        )
    )

    assert state.count_posts_on_date("2026-03-04") == 1
    assert state.count_posts_on_date("2026-03-05") == 1
    assert state.count_posts_on_date("2026-03-06") == 0
