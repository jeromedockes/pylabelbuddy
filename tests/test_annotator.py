from unittest.mock import MagicMock

from labelbuddy import _annotator


def test_annotator(example_text, root):
    annotations_manager = MagicMock()
    annotations_manager.add_annotation.side_effect = range(1, 10)
    annotator = _annotator.Annotator(root, annotations_manager)
    annotations_manager.content = example_text
    annotations_manager.label_colors = {}
    annotator.refresh()
    assert annotator.text.text.get("1.0", "end") == example_text + "\n"
    assert hasattr(annotator.label_choices, "empty_banner")
    annotations_manager.label_colors = {
        "label 1": "#112233",
        "label 2": "#aabbcc",
    }
    annotator.refresh()
    assert len(annotator.label_choices.label_buttons) == 2
    annotator.text.search_box.search_string.set("Nunc")
    # call callbacks bound to <<Searching>> and <<Selection>>
    annotator._deactivate_region()
    annotator._set_selection_button_states()
    assert annotator.label_choices.delete_button["state"] == "disabled"
    for button in annotator.label_choices.label_buttons:
        assert button["state"] == "normal"
    annotator.label_choices.selected_label.set("label 1")
    annotator._set_label_for_selection()
    assert annotator.label_choices.delete_button["state"] == "normal"
    lregion = annotator.labelled_regions[
        list(annotator.labelled_regions.keys())[0]
    ]
    assert lregion["label"] == "label 1"
    label, start, end = annotations_manager.add_annotation.call_args[0]
    assert label == "label 1"
    assert example_text[start:end] == "Nunc"

    annotator.label_choices.selected_label.set("label 2")
    annotator._set_label_for_selection()
    assert annotations_manager.update_annotation_label.call_args[0] == (
        "1",
        "label 2",
    )
    annotator._deactivate_region()
    assert annotator.label_choices.delete_button["state"] == "disabled"
    for button in annotator.label_choices.label_buttons:
        assert button["state"] == "disabled"

    annotator.text.text.tag_add("sel", "1.0", "end")
    annotator._set_selection_button_states()
    annotator.label_choices.selected_label.set("label 1")
    annotator._set_label_for_selection()
    regions = annotator.labelled_regions
    assert len(regions) == 1
    annotator._deactivate_region()
    click_event = MagicMock()
    click_event.x, click_event.y = 10, 10
    annotator._activate_region(click_event)
    assert annotator.active_labelled_region == "2"
    annotator._delete_active_region()
    assert annotator.labelled_regions == {}
    assert annotations_manager.delete_annotation.call_args[0] == ("2",)
    annotations_manager.existing_regions.return_value = [(3, "label 3", 0, 5)]
    annotations_manager.label_colors = {
        "label 3": "#112233",
    }

    annotator._load_existing_regions()
    ranges = annotator.text.text.tag_ranges("3")
    assert tuple(map(str, ranges)) == ("1.0", "1.5")
