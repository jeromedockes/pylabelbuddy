from unittest.mock import MagicMock
import pytest

from labelbuddy import _dataset_manager, _database


def fill_db(data_dir):
    _database.add_docs_from_file(data_dir / "docs_1.csv")
    _database.add_labels_from_json(data_dir / "labels_1.json")


@pytest.fixture
def ask_patch(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("tkinter.messagebox", mock)
    return mock


@pytest.fixture
def fdialog_patch(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("tkinter.filedialog", mock)
    return mock


@pytest.fixture
def toplevel_patch(monkeypatch):
    pb_mock = MagicMock()
    monkeypatch.setattr("tkinter.ttk.Progressbar", pb_mock)
    mock = MagicMock()
    monkeypatch.setattr("tkinter.Toplevel", mock)
    return mock


def test_dataset_manager(
    root,
    prepare_db,
    data_dir,
    example_docs,
    example_labels,
    ask_patch,
    fdialog_patch,
    toplevel_patch,
    monkeypatch,
):
    manager = _dataset_manager.DatasetManager(root)
    assert manager.total_n_docs() == 30
    assert manager.total_n_docs("labelled docs") == 0
    assert manager.total_n_docs("unlabelled docs") == 30
    new_db = data_dir / "new_db.sqlite"
    _database.set_db_path(new_db)
    con = _database.get_connection()
    manager.change_database()
    assert manager.total_n_docs() == 0
    fill_db(data_dir)
    with con:
        con.executemany(
            "insert into annotation (doc_id, label_id, start_char, end_char)"
            " values (?, ?, ?, ?)",
            [(7, 1, 2, 5), (10, 3, 5, 9)],
        )
    assert manager.total_n_docs("labelled docs") == 2
    assert manager.total_n_docs("unlabelled docs") == 28
    docs = manager.get_docs()
    assert len(docs) == 10
    assert [d["id"] for d in docs] == list(range(1, 11))
    docs = manager.get_docs(doc_filter="labelled docs")
    assert [d["id"] for d in docs] == [7, 10]
    labels = manager.get_labels()
    assert len(labels) == len(example_labels)
    ask_patch.askokcancel.return_value = False
    label_ids = con.execute("select id from label order by id").fetchall()
    labels = con.execute("select string_form from label").fetchall()
    docs = con.execute("select content from document").fetchall()
    doc_ids = con.execute("select id from document order by id").fetchall()
    manager.delete_labels([1, 2])
    manager.delete_docs([1, 2])
    manager.delete_all_docs()
    new_label_ids = con.execute("select id from label order by id").fetchall()
    new_doc_ids = con.execute("select id from document order by id").fetchall()
    assert label_ids == new_label_ids
    assert doc_ids == new_doc_ids
    ask_patch.askokcancel.return_value = True
    manager.delete_labels([1, 2])
    manager.delete_docs([1, 2])
    new_label_ids = con.execute("select id from label order by id").fetchall()
    new_doc_ids = con.execute("select id from document order by id").fetchall()
    assert new_label_ids == label_ids[2:]
    assert new_doc_ids == doc_ids[2:]
    manager.delete_all_docs()
    assert con.execute("select * from document").fetchone() is None
    fdialog_patch.askopenfilename.return_value = data_dir / "labels_1.json"
    manager.import_labels()
    new_labels = con.execute("select string_form from label").fetchall()
    assert set(new_labels) == set(labels)
    fdialog_patch.askopenfilename.return_value = data_dir / "docs_1.csv"
    manager.import_documents()
    new_docs = con.execute("select content from document").fetchall()
    assert set(new_docs) == set(docs)
    monkeypatch.setattr("getpass.getuser", lambda *args: "hello-user")
    assert manager.suggest_approver_name() == "hello-user"
    with con:
        con.executemany(
            "insert into annotation (doc_id, label_id, start_char, end_char)"
            " values (?, ?, ?, ?)",
            [
                (3, 8, 20, 80),
                (8, 3, 50, 40),
                (8, 5, 15, 50),
            ],
        )
    fdialog_patch.asksaveasfilename.return_value = data_dir / "exported.json"
    manager.export_documents()
    loaded = _database.read_json_docs(data_dir / "exported.json")
    assert len(loaded) == 2
    assert loaded[1]["labels"][1][0] == 15
