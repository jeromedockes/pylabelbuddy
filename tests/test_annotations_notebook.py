from labelbuddy import _annotations_notebook


def test_annotations_notebook(root, annotations_mock, dataset_mock):
    nb = _annotations_notebook.AnnotationsNotebook(
        root, annotations_mock, dataset_mock
    )
    nb.change_database()
    assert nb.notebook.index(nb.notebook.select()) == 2
    nb.go_to_annotations()
    assert nb.notebook.index(nb.notebook.select()) == 0
