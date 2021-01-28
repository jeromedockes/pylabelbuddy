import json
from labelbuddy import _database


def test_get_db_path(lb_dir):
    db_path = _database.get_default_db_path()
    assert db_path == lb_dir.joinpath("labelbuddy-data.sqlite3")
    new_db = lb_dir.joinpath("newdb.sql")
    _database.set_app_global_parameter("last_opened_database", str(new_db))
    db_path = _database.get_default_db_path()
    assert db_path == str(new_db)
    other_db = lb_dir.joinpath("otherdb")
    _database.set_db_path(str(other_db))
    db_path = _database.get_db_path()
    assert str(other_db) == db_path


def test_create_database():
    con = _database.get_connection()
    tables = con.execute(
        "select name from sqlite_master where type='table'"
    ).fetchall()
    tables = {t[0] for t in tables}
    assert tables == {
        "document",
        "label",
        "annotation",
        "app_state",
        "app_state_extra",
    }


def test_add_docs_from_csv(data_dir, fake_doc):
    _database.add_docs_from_file(data_dir / "docs_1.csv")
    _database.add_docs_from_file(data_dir / "docs_2.csv")
    con = _database.get_connection()
    docs = con.execute("select * from document").fetchall()
    assert len(docs) == 33
    assert docs[0]["content"] == fake_doc["text"]


def test_add_docs_from_txt(data_dir, fake_doc):
    _database.add_docs_from_file(data_dir / "docs_1.txt")
    con = _database.get_connection()
    docs = con.execute("select * from document").fetchall()
    assert len(docs) == 30
    assert docs[0]["content"] == fake_doc["text"].replace("\n", "\t") + "\n"


def test_add_labels_from_json(data_dir):
    _database.add_labels_from_json(data_dir / "labels_1.json")
    con = _database.get_connection()
    labels = con.execute("select * from label order by rowid").fetchall()
    json_labels = json.loads((data_dir / "labels_1.json").read_text())
    assert [label["string_form"] for label in labels] == [
        label["text"] for label in json_labels
    ]


def test_export_annotations(data_dir, fake_doc):
    _database.add_docs_from_file(data_dir / "docs_1.csv")
    _database.add_labels_from_json(data_dir / "labels_1.json")
    con = _database.get_connection()
    with con:
        con.execute(
            "insert into annotation (doc_id, label_id, start_char, end_char)"
            " values (1, 2, 2, 4)"
        )
    export_file = data_dir / "exported.json"
    _database.export_annotations(export_file, approver="me")
    loaded = _database.read_json_docs(export_file)
    assert len(loaded) == 1
    assert loaded[0]["text"] == fake_doc["text"]
    assert loaded[0]["annotation_approver"] == "me"
    assert loaded[0]["labels"] == [[2, 4, "something-else"]]
    assert loaded[0]["extra_data"] == {
        "id": "8533",
        "title": "\u0641\nb ",
        "keywords": "",
    }


def test_set_app_state_extra():
    someval = _database.get_app_state_extra("somekey", "hello")
    assert someval == "hello"
    someval = _database.get_app_state_extra("somekey")
    assert someval is None
    _database.set_app_state_extra("somekey", 345)
    someval = _database.get_app_state_extra("somekey")
    assert someval == 345
