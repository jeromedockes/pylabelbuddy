from pylabelbuddy import _annotations_manager, _database


def fill_db(data_dir):
    _database.add_docs_from_file(data_dir / "docs_1.csv")
    _database.add_labels_from_json(data_dir / "labels_1.json")


def test_annotations_manager(root, data_dir, prepare_db):
    manager = _annotations_manager.AnnotationsManager(root)
    assert manager.n_docs() == 30
    new_db = data_dir / "new_db.sqlite"
    _database.set_db_path(new_db)
    con = _database.get_connection()
    manager.change_database()
    assert manager.n_docs() == 0
    manager.visit_document(1)
    assert manager.current_doc_id is None
    for direction in ["prev", "next"]:
        for kind in ["", "_labelled", "_unlabelled"]:
            getattr(manager, f"visit_{direction}{kind}")()
            assert manager.current_doc_id is None
    fill_db(data_dir)
    labels = manager.labels_info
    assert len(labels) == 8
    assert labels["something"] == {"id": 1, "color": "#ff00ff"}
    manager.visit_document()
    assert manager.current_doc_id == 1
    manager.visit_document(2)
    assert manager.current_doc_id == 2
    assert (
        manager.content
        == con.execute("select content from document where id = 2").fetchone()[
            "content"
        ]
    )
    manager.visit_document(2000)
    assert manager.current_doc_id == 2
    with con:
        con.execute("update app_state set last_visited_doc = null")
    manager.visit_document(2000)
    assert manager.current_doc_id == 1
    assert (
        con.execute("select last_visited_doc from app_state").fetchone()[0]
        == 1
    )
    with con:
        con.executemany(
            "insert into annotation (doc_id, label_id, start_char, end_char)"
            " values (?, ?, ?, ?)",
            [(7, 1, 2, 5), (10, 3, 5, 9)],
        )
    manager.visit_next()
    assert manager.current_doc_id == 2
    manager.visit_next_labelled()
    assert manager.current_doc_id == 7
    manager.visit_next_labelled()
    assert manager.current_doc_id == 10
    manager.visit_prev_unlabelled()
    assert manager.current_doc_id == 9
    manager.visit_prev_labelled()
    assert manager.current_doc_id == 7
    manager.visit_prev_labelled()
    assert manager.current_doc_id == 7
    manager.visit_prev_unlabelled()
    assert manager.current_doc_id == 6
    manager.visit_prev()
    assert manager.current_doc_id == 5
    manager.visit_document(6)
    manager.visit_next_unlabelled()
    assert manager.current_doc_id == 8
    with con:
        con.execute("delete from document where id = 8")
    manager.refresh()
    assert manager.current_doc_id == 1
    manager.visit_document(1)
    manager.visit_prev()
    assert manager.current_doc_id == 1
    manager.visit_prev_labelled()
    assert manager.current_doc_id == 1
    manager.visit_prev_unlabelled()
    assert manager.current_doc_id == 1
    manager.visit_document(30)
    manager.visit_next()
    assert manager.current_doc_id == 30
    manager.visit_next_labelled()
    assert manager.current_doc_id == 30
    manager.visit_next_unlabelled()
    assert manager.current_doc_id == 30

    assert len(list(manager.existing_regions())) == 0
    manager.visit_document(7)
    assert len(list(manager.existing_regions())) == 1
    assert manager.add_annotation("something-else", 0, 1) == 3
    assert manager.add_annotation("unknown label", 0, 1) is None
    assert len(list(manager.existing_regions())) == 2
    manager.delete_annotation("1")
    assert len(list(manager.existing_regions())) == 1
    manager.delete_annotation("3")
    assert len(list(manager.existing_regions())) == 0
    manager.visit_prev()
    manager.visit_next_labelled()
    assert manager.current_doc_id == 10
    manager.update_annotation_label("2", "unknown label")
    manager.update_annotation_label("2", "something-else")
    assert (
        con.execute(
            "select label_id from annotation where rowid = 2"
        ).fetchone()[0]
        == 2
    )
    assert manager.last_doc() == 30
    assert manager.first_doc() == 1
    assert manager.first_unlabelled() == 1
    assert manager.last_unlabelled() == 30
    assert manager.first_labelled() == 10
    assert manager.last_labelled() == 10
