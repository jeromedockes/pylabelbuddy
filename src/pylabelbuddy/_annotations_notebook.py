import tkinter as tk
import tkinter.ttk

from pylabelbuddy import _database
from pylabelbuddy._annotations_navigator import AnnotationsNavigator
from pylabelbuddy._dataset_menu import DatasetMenu
from pylabelbuddy._import_export_menu import ImportExportMenu


class AnnotationsNotebook(tk.Frame):
    def __init__(self, parent, annotations_manager, dataset, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.annotations_manager = annotations_manager
        self.dataset = dataset
        self.notebook = tk.ttk.Notebook(self)
        self.annotations_page = AnnotationsNavigator(
            self.notebook, self.annotations_manager
        )
        self.dataset_page = DatasetMenu(self.notebook, self.dataset)
        self.import_export_page = ImportExportMenu(self.notebook, self.dataset)
        self.notebook.add(self.annotations_page, text="Annotate")
        self.notebook.add(self.dataset_page, text="Dataset")
        self.notebook.add(self.import_export_page, text="Import / Export")
        self.annotations_manager.bind(
            "<<DocumentStatusChanged>>",
            self.dataset_page.documents_list.fill,
            add=True,
        )
        self.dataset.bind(
            "<<LabelsChanged>>", self.annotations_page.refresh, add=True
        )
        self.dataset.bind(
            "<<DocumentsChanged>>", self.annotations_manager.refresh, add=True
        )
        self.dataset_page.documents_list.bind(
            "<<AnnotateRequest>>", self.go_to_annotations, add=True
        )
        self.notebook.bind(
            "<<NotebookTabChanged>>", self._focus_search, add=True
        )
        self.notebook.bind(
            "<<NotebookTabChanged>>",
            self._store_notebook_page_selection,
            add=True,
        )
        self.notebook.select(
            int(_database.get_app_state_extra("notebook_page", 2))
        )
        self.notebook.grid(sticky="NSEW")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def change_database(self, *args):
        self.notebook.select(
            int(_database.get_app_state_extra("notebook_page", 2))
        )

    def _store_notebook_page_selection(self, *args):
        _database.set_app_state_extra(
            "notebook_page", self.notebook.index(self.notebook.select())
        )

    def go_to_annotations(self, *args):
        try:
            doc_id = self.dataset_page.documents_list.requested_doc_id
            self.annotations_manager.visit_document(doc_id)
        except AttributeError:
            pass
        self.notebook.select(0)

    def _focus_search(self, *args):
        if self.notebook.index(self.notebook.select()) == 0:
            text = self.annotations_page.annotator.text
            text.search_box.entry_box.focus_set()
