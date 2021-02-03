from unittest.mock import MagicMock
from labelbuddy import _dataset_menu


class _DB:
    def __init__(self):
        self.lab_ids = list(range(7, 40, 4))
        self.unlab_ids = list(range(9, 59, 4))
        self.all_ids = sorted(self.lab_ids + self.unlab_ids)
        self.doc_ids = {
            "all docs": self.all_ids,
            "unlabelled docs": self.unlab_ids,
            "labelled docs": self.lab_ids,
        }

    def get_docs(self, offset, page_size, doc_filter):
        docs_ids = self.doc_ids[doc_filter][offset : offset + page_size]
        return [
            {"id": doc_id, "trunc_content": f"doc {doc_id} {doc_filter}"}
            for doc_id in docs_ids
        ]

    def n_docs(self, doc_filter):
        return len(self.get_docs(0, 1000, doc_filter))


def test_documents_list(root, example_labels):
    db = _DB()
    assert db.n_docs("all docs") == 22
    assert db.n_docs("labelled docs") == 9
    assert db.n_docs("unlabelled docs") == 13
    manager = MagicMock()
    manager.get_labels.return_value = [
        {"id": i + 1, "string_form": la["text"], "color": "#aabbcc"}
        for i, la in enumerate(example_labels)
    ]
    manager.total_n_docs.side_effect = db.n_docs
    manager.get_docs.side_effect = db.get_docs
    menu = _dataset_menu.DatasetMenu(root, manager)
    doc_list = menu.documents_list
    doc_list.page_size = 4
    doc_list.fill()
    assert doc_list.docs_info == db.get_docs(0, 4, "all docs")
    doc_list.next_page()
    assert doc_list.docs_info == db.get_docs(4, 4, "all docs")
    doc_list.next_page()
    assert doc_list.offset == 8
    doc_list.doc_filter.set("labelled docs")
    doc_list._filter_change()
    assert doc_list.offset == 0
    doc_list.last_page()
    assert doc_list.offset == 8
    doc_list.next_page()
    doc_list.next_page()
    assert doc_list.offset == 8
    assert len(doc_list.docs_info) == 1
    assert doc_list.docs_info == db.get_docs(8, 4, "labelled docs")
    doc_list.docs_list.listbox.selection_set(0)
    doc_list.go_to_annotations()
    assert doc_list.requested_doc_id == 39
    doc_list.delete_selection()
    assert manager.delete_docs.call_args[0] == ([39],)
    doc_list.prev_page()
    assert doc_list.offset == 4
    doc_list.first_page()
    assert doc_list.offset == 0
    manager.total_n_docs.side_effect = lambda *args: 0
    doc_list.fill()
    assert hasattr(doc_list, "empty_banner")


def test_labels_list(root, example_labels, monkeypatch):
    color_chooser = MagicMock()
    color_chooser.return_value = ((1, 2, 3), "#010203")
    monkeypatch.setattr("tkinter.colorchooser.askcolor", color_chooser)
    db = _DB()
    manager = MagicMock()
    labels = [
        {"id": i + 1, "string_form": la["text"], "color": "#aabbcc"}
        for i, la in enumerate(example_labels)
    ]
    manager.get_labels.return_value = labels
    manager.total_n_docs.side_effect = db.n_docs
    manager.get_docs.side_effect = db.get_docs
    menu = _dataset_menu.DatasetMenu(root, manager)
    lab_list = menu.labels_list
    assert lab_list.labels_info == labels
    lab_list.labels_list.listbox.selection_set([1])
    lab_list.labels_list.listbox.selection_set([3])
    lab_list._update_button_states()
    assert lab_list.delete_button["state"] == "normal"
    lab_list._set_color_for_selection()
    assert manager.set_label_color.call_args[0] == (
        labels[1]["id"],
        "#010203",
    )
    lab_list.delete_selection()
    assert manager.delete_labels.call_args[0] == (
        [labels[1]["id"], labels[3]["id"]],
    )
    manager.get_labels.side_effect = lambda *args: []
    lab_list.fill()
    assert hasattr(lab_list, "empty_banner")
