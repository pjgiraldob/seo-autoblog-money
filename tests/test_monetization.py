from seo_factory.monetization import select_affiliate_items


def test_select_affiliate_items_keyword_first():
    cfg = {
        "default_disclaimer": "d",
        "by_keyword": {"seo": [{"name": "A", "url": "https://a"}]},
        "by_category": {"blog": [{"name": "B", "url": "https://b"}]},
        "fallback": [{"name": "C", "url": "https://c"}],
    }
    items, disclaimer = select_affiliate_items(cfg, tags=["seo"], categories=["blog"], max_items=3)
    assert items[0]["url"] == "https://a"
    assert disclaimer == "d"


def test_select_affiliate_items_fallback():
    cfg = {
        "default_disclaimer": "d",
        "by_keyword": {},
        "by_category": {},
        "fallback": [{"name": "C", "url": "https://c"}],
    }
    items, _ = select_affiliate_items(cfg, tags=["x"], categories=["y"], max_items=3)
    assert items[0]["url"] == "https://c"
