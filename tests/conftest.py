import random
import csv
import json
from unittest.mock import MagicMock
import tkinter as tk

import pytest


@pytest.fixture(scope="function")
def root():
    tk_root = tk.Tk()
    yield tk_root
    tk_root.destroy()


@pytest.fixture
def annotations_mock():
    annotations_manager = MagicMock()
    annotations_manager.first_doc.return_value = 2
    annotations_manager.last_doc.return_value = 123
    annotations_manager.first_labelled.return_value = 7
    annotations_manager.last_labelled.return_value = 123
    annotations_manager.first_unlabelled.return_value = 2
    annotations_manager.last_unlabelled.return_value = 32
    annotations_manager.current_doc_id = 9
    return annotations_manager


@pytest.fixture
def dataset_mock():
    dataset_manager = MagicMock()
    dataset_manager.get_labels.return_value = []
    dataset_manager.get_docs.return_value = []
    dataset_manager.total_n_docs.return_value = 0
    return dataset_manager


@pytest.fixture
def prepare_db(data_dir):
    fill_db(data_dir)


def fill_db(data_dir):
    from labelbuddy import _database

    _database.add_docs_from_file(data_dir / "docs_1.csv")
    _database.add_labels_from_json(data_dir / "labels_1.json")


@pytest.fixture
def data_dir(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    docs_1 = list(make_fake_docs())
    docs_2 = list(make_fake_docs(4, 1))
    for i, docs in enumerate([docs_1, docs_2]):
        with open(
            data / f"docs_{i + 1}.csv", "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=list(docs[0].keys()))
            writer.writeheader()
            writer.writerows(docs)
        with open(data / f"docs_{i + 1}.txt", "w", encoding="utf-8") as f:
            for doc in docs:
                f.write(doc["text"].replace("\n", "\t"))
                f.write("\n")
    (data / "labels_1.json").write_text(
        json.dumps(get_labels()), encoding="utf-8"
    )
    (data / "labels_2.json").write_text(
        json.dumps([{"text": "newlabel", "background_color": "#aabbcc"}]),
        encoding="utf-8",
    )
    return data


@pytest.fixture(autouse=True, scope="function")
def fake_home(tmp_path, monkeypatch):
    home_dir = tmp_path.joinpath("temp_home")
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("USERPROFILE", str(home_dir))
    return home_dir


@pytest.fixture(scope="function")
def lb_dir(fake_home):
    return fake_home.joinpath(".labelbuddy")


@pytest.fixture(autouse=True, scope="function")
def reset_db_path(monkeypatch):
    monkeypatch.delattr(
        "labelbuddy._database.get_db_path.db_path", raising=False
    )


@pytest.fixture
def fake_doc():
    return list(make_fake_docs(1))[0]


@pytest.fixture
def example_docs():
    return list(make_fake_docs())


def make_fake_docs(n_docs=37, seed=0):
    rng = random.Random(seed)
    chars = """abD éô\r
\t\nف𝟂"""
    for i in range(n_docs):
        if not (i - 1) % 5:
            yield {"text": "", "title": None}
        else:
            doc_len = rng.randint(40, 300)
            doc = "".join(rng.choices(chars, k=doc_len))
            title_len = rng.randint(0, 9)
            title = "".join(rng.choices(chars, k=title_len))
            doc_id = rng.randint(0, 10000)
            yield {"text": doc, "id": doc_id, "title": title, "keywords": None}


@pytest.fixture
def example_labels():
    return get_labels()


def get_labels():
    return [
        {"text": "something", "background_color": "#ff00ff"},
        {"text": "something-else", "background_color": "blue"},
        {"text": "  ", "what": 3},
        {"text": "other_label", "backgroud_color": "#234"},
        {
            "id": 56,
            "text": "discard this",
            "prefix_key": None,
            "suffix_key": "x",
            "background_color": "",
            "text_color": "#ffffff",
        },
        {
            "id": 59,
            "text": "n pixels é '",
            "prefix_key": None,
            "suffix_key": "v",
            "background_color": "invalid-col",
            "text_color": "#ffffff",
        },
        {
            "id": 58,
            "text": "smoothing_",
            "prefix_key": None,
            "suffix_key": "s",
            "background_color": "#4F1B9A",
            "text_color": "#ffffff",
        },
        {
            "text": ";ariajeoria.",
            "prefix_key": None,
            "suffix_key": "c",
            "background_color": "#FFEB3B",
            "text_color": "#ffffff",
        },
    ]


@pytest.fixture
def example_text():
    return """Nullam eu ante vel est convallis dignissim. Fusce suscipit, wisi
facilisis facilisis, est dui fermentum leo, quis tempor ligula erat quis odio.
Nunc porta vulputate tellus. Nunc rutrum turpis sed pede. Sed bibendum. Aliquam
posuere. Nunc aliquet, augue nec adipiscing interdum, lacus tellus malesuada
massa, quis varius mi purus non odio. Pellentesque condimentum, magna ut
    maçã1, maçã2



suscipit hendrerit, maçã ipsum augue ornare nulla, non luctus diam neque sit
amet urna. Curabitur vulputate vestibulum lorem. Fusce sagittis, libero non
molestie mollis, magna orci ultrices dolor, at vulputate neque nulla lacinia
eros. Sed id ligula quis est convallis tempor. Curabitur lacinia pulvinar nibh.
Nam a sapien.


\tmaçã3

"""
