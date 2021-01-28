from unittest.mock import MagicMock

from labelbuddy import _annotations_navigator


def test_annotations_navigator(root):
    annotations_manager = MagicMock()
    annotations_manager.first_doc.return_value = 2
    annotations_manager.last_doc.return_value = 123
    annotations_manager.first_labelled.return_value = 7
    annotations_manager.last_labelled.return_value = 123
    annotations_manager.first_unlabelled.return_value = 2
    annotations_manager.last_unlabelled.return_value = 32
    annotations_manager.current_doc_id = 9
    navigator = _annotations_navigator.AnnotationsNavigator(
        root, annotations_manager
    )
    for button_name in ["", "labelled_", "unlabelled_"]:
        for direction in ["prev", "next"]:
            assert (
                getattr(navigator.nav_bar, f"{direction}_{button_name}button")[
                    "state"
                ]
                == "normal"
            )
    annotations_manager.current_doc_id = 5
    navigator.refresh()
    assert navigator.nav_bar.prev_labelled_button["state"] == "disabled"
