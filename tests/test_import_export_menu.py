from unittest.mock import MagicMock
from pylabelbuddy import _import_export_menu


def test_export_menu(root):
    dataset = MagicMock()
    ie_menu = _import_export_menu.ImportExportMenu(root, dataset)
    ie_menu.export_menu.change_database()
    assert dataset.suggest_approver_name.call_count == 2
    ie_menu.export_menu._export()
    assert dataset.export_documents.call_args[1]["labelled_only"]
    ie_menu.export_menu.labelled_only.set(False)
    ie_menu.export_menu._export()
    assert not dataset.export_documents.call_args[1]["labelled_only"]
