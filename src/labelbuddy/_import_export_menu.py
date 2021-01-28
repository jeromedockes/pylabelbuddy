import tkinter as tk
import tkinter.messagebox


class ImportMenu(tk.LabelFrame):
    def __init__(self, parent, dataset, *args, text="Importing", **kwargs):
        super().__init__(parent, *args, text=text, **kwargs)
        self.dataset = dataset
        self.import_docs_button = tk.Button(
            self,
            text="Import docs",
            command=self.dataset.import_documents,
        )
        self.import_labels_button = tk.Button(
            self,
            text="Import labels",
            command=self.dataset.import_labels,
        )
        self.import_docs_button.grid(row=0, column=0, padx=5, pady=5)
        self.import_labels_button.grid(row=0, column=1, padx=5, pady=5)
        try:
            self["padx"] = 10
            self["pady"] = 10
        except Exception:
            pass


class ExportMenu(tk.LabelFrame):
    def __init__(self, parent, dataset, *args, text="Exporting", **kwargs):
        super().__init__(parent, *args, text=text, **kwargs)
        self.dataset = dataset
        self.default_name = self.dataset.suggest_approver_name()
        self.labelled_only = tk.BooleanVar(value=True)
        self.labelled_only_button = tk.Checkbutton(
            self,
            text="Export only annotated documents",
            variable=self.labelled_only,
            onvalue=True,
            offvalue=False,
        )
        self.approver_label = tk.Label(
            self, text="Annotation approver (optional):  "
        )
        self.approver_name = tk.StringVar(value=self.default_name)
        self.approver_name_entry = tk.Entry(
            self, textvariable=self.approver_name
        )
        self.export_button = tk.Button(
            self, text="Export", command=self._export
        )
        self.labelled_only_button.grid(
            row=0, column=0, columnspan=2, sticky="W"
        )
        self.dataset.bind(
            "<<DefaultAnnotatorChanged>>", self.change_database, add=True
        )
        self.approver_label.grid(row=1, column=0, sticky="W")
        self.approver_name_entry.grid(row=1, column=1, sticky="W")
        self.export_button.grid(
            row=2, column=0, columnspan=2, sticky="W", padx=5, pady=5
        )

        try:
            self["padx"] = 10
            self["pady"] = 10
        except Exception:
            pass

    def change_database(self, *args):
        self.default_name = self.dataset.suggest_approver_name()
        self.approver_name.set(self.default_name)

    def _export(self, *args):
        approver_name = self.approver_name.get().strip() or None
        labelled_only = self.labelled_only.get()
        self.dataset.export_documents(
            labelled_only=labelled_only, approver_name=approver_name
        )


class ImportExportMenu(tk.Frame):
    def __init__(self, parent, dataset, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.dataset = dataset
        self.import_menu = ImportMenu(self, self.dataset)
        self.export_menu = ExportMenu(self, self.dataset)
        self.import_menu.grid(row=0, column=0, sticky="W", padx=10, pady=10)
        self.export_menu.grid(row=1, column=0, sticky="W", padx=10, pady=10)
