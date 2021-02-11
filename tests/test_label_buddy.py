from unittest.mock import MagicMock

import pytest

from pylabelbuddy import _label_buddy, _database


def test_label_buddy(root, tmp_path, monkeypatch):
    fd_mock = MagicMock()
    monkeypatch.setattr("tkinter.filedialog", fd_mock)
    mb_mock = MagicMock()
    monkeypatch.setattr("tkinter.messagebox", mb_mock)
    wb_mock = MagicMock()
    monkeypatch.setattr("webbrowser.open", wb_mock)
    buddy = _label_buddy.LabelBuddy(tmp_path / "db.sqlite")
    new_db = tmp_path / "db1.sqlite"
    fd_mock.askopenfilename.return_value = new_db
    fd_mock.asksaveasfilename.return_value = new_db
    buddy._open_new_database()
    assert buddy.db_path == new_db
    assert new_db.is_file
    buddy._open_database(True)
    assert buddy.db_path == new_db
    buddy._show_about_info()
    mb_mock.showinfo.assert_called_once()
    buddy._go_to_doc_in_browser()
    wb_mock.assert_called_once()
    base_offset = _database.get_app_global_parameters().get(
        "font_size_offset", 0
    )
    dialog, plus_minus = buddy._set_font()
    for i in range(7):
        plus_minus._increase_font()
    new_offset = _database.get_app_global_parameters().get(
        "font_size_offset", 0
    )
    assert new_offset == base_offset + 7
    for i in range(3):
        plus_minus._decrease_font()
    new_offset = _database.get_app_global_parameters().get(
        "font_size_offset", 0
    )
    assert new_offset == base_offset + 4
    dialog.destroy()
    buddy._store_geometry_and_close()
    exit_mock = MagicMock()
    exit_mock.side_effect = Exception("exiting")
    monkeypatch.setattr("sys.exit", exit_mock)
    with pytest.raises(Exception, match="exiting"):
        _label_buddy.start_label_buddy(["--version"])
    exit_mock.assert_called_once()
