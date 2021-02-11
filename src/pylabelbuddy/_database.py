import sys
import random
import re
import csv
import json
import sqlite3
from pathlib import Path


def get_data_dir():
    data_dir = Path().home() / ".pylabelbuddy"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_default_db_path():
    last_opened = get_app_global_parameters().get("last_opened_database", None)
    if last_opened:
        return last_opened
    return get_data_dir() / "pylabelbuddy-data.sqlite3"


def get_app_global_parameters():
    try:
        return json.loads(
            (get_data_dir() / "params.json").read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        return {}


def set_app_global_parameter(key, value):
    params = get_app_global_parameters()
    params[key] = value
    (get_data_dir() / "params.json").write_text(
        json.dumps(params), encoding="utf-8"
    )


def get_db_path():
    if getattr(get_db_path, "db_path", None) is not None:
        return get_db_path.db_path
    return get_default_db_path()


def set_db_path(db_path):
    get_db_path.db_path = db_path


def _create_database(con):
    script = (
        Path(__file__)
        .parent.joinpath("_data", "create_database.sql")
        .read_text(encoding="utf-8")
    )
    with con:
        con.executescript(script)


class ClosingConnection:
    def __init__(self, connection):
        self.connection = connection

    def close(self, *args, **kwargs):
        return self.connection.close(*args, **kwargs)

    def execute(self, *args, **kwargs):
        return self.connection.execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        return self.connection.executemany(*args, **kwargs)

    def executescript(self, *args, **kwargs):
        return self.connection.executescript(*args, **kwargs)

    def __enter__(self, *args, **kwargs):
        return self.connection.__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        return self.connection.__exit__(*args, **kwargs)

    def __del__(self):
        try:
            self.connection.close()
        except Exception as e:
            print(e)


def get_connection():
    con = ClosingConnection(sqlite3.connect(str(get_db_path())))
    con.execute("PRAGMA foreign_keys = 1")
    con.connection.row_factory = sqlite3.Row
    _create_database(con)
    return con


def add_docs_from_file(file_path, progress_bar=None):
    if str(file_path).endswith(".csv"):
        add_docs_from_csv(file_path, progress_bar=progress_bar)
    else:
        add_docs_from_txt(file_path, progress_bar=progress_bar)


def _set_csv_max_size():
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = max_int // 10


def add_docs_from_csv(csv_path, progress_bar=None):
    _set_csv_max_size()
    file_size = Path(csv_path).stat().st_size
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        _add_docs(reader, file_size=file_size, progress_bar=progress_bar)


def add_docs_from_txt(txt_path, progress_bar=None):
    file_size = Path(txt_path).stat().st_size
    with open(txt_path, encoding="utf-8", newline="\n") as f:
        _add_docs(
            ({"text": text_line} for text_line in f),
            file_size=file_size,
            progress_bar=progress_bar,
        )
    if progress_bar is not None:
        progress_bar.configure(value=file_size)
        progress_bar.winfo_toplevel().update_idletasks()


def _add_docs(docs, file_size=None, progress_bar=None):
    con = get_connection()
    approx_seen_bytes = 0
    if progress_bar is not None:
        progress_bar.configure(maximum=file_size)
        progress_bar.configure(value=0)
    for doc in docs:
        first_key = list(doc.keys())[0]
        for val in doc.values():
            try:
                approx_seen_bytes += len((val or b"").encode("utf-8"))
            except Exception:
                pass
        content = doc[first_key]
        del doc[first_key]
        json_extra = json.dumps(doc)
        try:
            with con:
                con.execute(
                    "insert into document (content, extra_data) "
                    "values (?, ?)",
                    (content, json_extra),
                )
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                print(f"doc already in database: '{content[:20]} ...'")
            else:
                print(f"Failed to insert doc: '{content[:20]}'")
        except sqlite3.Error:
            print(f"Failed to insert doc: '{content[:20]}'")
        if progress_bar is not None:
            progress_bar.configure(value=approx_seen_bytes)
            progress_bar.winfo_toplevel().update_idletasks()


def read_labels_from_json(labels_json):
    labels = json.loads(Path(labels_json).read_text(encoding="utf-8"))
    return [
        {
            "string_form": label["text"],
            "color": label.get("background_color", ""),
        }
        for label in labels
    ]


def _check_color(color):
    mpl_tab_colors = [
        "#aec7e8",
        "#ffbb78",
        "#98df8a",
        "#ff9896",
        "#c5b0d5",
        "#c49c94",
        "#f7b6d2",
        "#c7c7c7",
        "#dbdb8d",
        "#9edae5",
    ]
    if re.match(r"#[0-9a-fA-F]{6}", color):
        return color.lower()
    new_color = mpl_tab_colors[random.randint(0, len(mpl_tab_colors) - 1)]
    print(f"Unknown color: {color}; replacing with random value: {new_color}")
    return new_color


def add_labels_from_json(labels_json):
    con = get_connection()
    for label in read_labels_from_json(labels_json):
        label["color"] = _check_color(label["color"])
        try:
            with con:
                con.execute(
                    "insert into label (string_form, color) values "
                    "(:string_form, :color)",
                    label,
                )
        except sqlite3.IntegrityError:
            print(f"label already in database: {label['string_form']}")
            already_in_db = True
        else:
            already_in_db = False
        if already_in_db:
            with con:
                con.execute(
                    "update label set color = :color where "
                    "string_form = :string_form",
                    label,
                )


def read_json_docs(file_path):
    """read json documents concatenated in a file"""
    content = Path(file_path).read_text(encoding="utf-8").strip()
    all_docs = []
    while content:
        doc, offset = json.JSONDecoder().raw_decode(content)
        all_docs.append(doc)
        content = content[offset:].strip()
    return all_docs


def export_annotations(output_file, labelled_docs_only=True, approver=None):
    con = get_connection()
    if labelled_docs_only:
        docs = con.execute("select id from labelled_document order by id")
    else:
        docs = con.execute("select id from document order by id")
    n_docs, n_annotations = 0, 0
    with open(output_file, "w", encoding="utf-8") as output:
        for doc in docs:
            n_docs += 1
            doc_info = con.execute(
                "select content, extra_data from document where id = ?",
                (doc["id"],),
            ).fetchone()
            doc_annotations = con.execute(
                "select string_form, start_char, end_char "
                "from annotation inner join label "
                "on annotation.label_id = label.id "
                "where annotation.doc_id = ? "
                "order by annotation.rowid",
                (doc["id"],),
            ).fetchall()
            doc_output = {
                "text": doc_info["content"],
                "extra_data": json.loads(doc_info["extra_data"]),
                "annotation_approver": approver,
                "labels": [],
            }
            doc_output["text"] = doc_info["content"]
            for annotation in doc_annotations:
                doc_output["labels"].append(
                    [
                        annotation["start_char"],
                        annotation["end_char"],
                        annotation["string_form"],
                    ]
                )
            n_annotations += len(doc_output["labels"])
            output.write(json.dumps(doc_output))
            output.write("\n")
    return {"n_docs": n_docs, "n_annotations": n_annotations}


def get_app_state_extra(key, default=None):
    con = get_connection()
    res = con.execute(
        "select value from app_state_extra where key = ?", (key,)
    ).fetchone()
    if res is None:
        return default
    return res[0]


def set_app_state_extra(key, value):
    con = get_connection()
    exists = con.execute(
        "select count(*) from app_state_extra where key = ?", (key,)
    ).fetchone()[0]
    if exists:
        with con:
            con.execute(
                "update app_state_extra set value = ? where key = ?",
                (value, key),
            )
    else:
        with con:
            con.execute(
                "insert into app_state_extra (key, value) values (?, ?)",
                (key, value),
            )
