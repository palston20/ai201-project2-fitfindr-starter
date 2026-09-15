from tools import search_listings, suggest_outfit, create_fit_card


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)

    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)

    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)

    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_empty_wardrobe():
    new_item = {
        "title": "Y2K Baby Tee — Butterfly Print",
        "price": 18.00,
        "platform": "Depop",
        "size": "M",
        "description": "Pink, purple, and white butterfly graphic baby tee",
    }

    wardrobe = {"items": []}

    result = suggest_outfit(new_item, wardrobe)

    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_create_fit_card_missing_outfit():
    new_item = {
        "title": "Y2K Baby Tee — Butterfly Print",
        "price": 18.00,
        "platform": "Depop",
        "size": "M",
    }

    result = create_fit_card("", new_item)

    assert isinstance(result, str)
    assert "Cannot write a fit card without an outfit suggestion" in result