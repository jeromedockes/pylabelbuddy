from pylabelbuddy import _searchable_text


def test_searchable_text(example_text):
    root = None
    text = example_text
    searchable_text = _searchable_text.SearchableText(root, None)
    searchable_text._fill(text)
    assert searchable_text.text["state"] == "disabled"

    searchable_text.search_box.search_string.set("maçã")
    selected = searchable_text.text.tag_ranges("sel")
    start = searchable_text.text.count("1.0", selected[0])[0]
    end = searchable_text.text.count("1.0", selected[1])[0]
    assert text[start : end + 1] == "maçã1"

    searchable_text._search_next()
    selected = searchable_text.text.tag_ranges("sel")
    start = searchable_text.text.count("1.0", selected[0])[0]
    end = searchable_text.text.count("1.0", selected[1])[0]
    assert text[start : end + 1] == "maçã2"

    searchable_text._search_prev()
    selected = searchable_text.text.tag_ranges("sel")
    start = searchable_text.text.count("1.0", selected[0])[0]
    end = searchable_text.text.count("1.0", selected[1])[0]
    assert text[start : end + 1] == "maçã1"

    searchable_text._search_prev()
    selected = searchable_text.text.tag_ranges("sel")
    start = searchable_text.text.count("1.0", selected[0])[0]
    end = searchable_text.text.count("1.0", selected[1])[0]
    assert text[start : end + 1] == "maçã3"
