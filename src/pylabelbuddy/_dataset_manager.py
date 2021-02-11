import getpass
import tkinter as tk
import tkinter.ttk
import tkinter.filedialog
import tkinter.messagebox

from pylabelbuddy import _database, _utils


class DatasetManager(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = _database.get_connection()

    def change_database(self, *args):
        self.connection = _database.get_connection()
        self.event_generate("<<LabelsChanged>>")
        self.event_generate("<<DocumentsChanged>>")
        self.event_generate("<<DefaultAnnotatorChanged>>")

    def get_labels(self):
        results = self.connection.execute(
            "select id, string_form, color FROM label order by id"
        ).fetchall()
        return results

    def delete_labels(self, label_ids):
        sing = len(label_ids) == 1
        resp = tk.messagebox.askokcancel(
            message=f"Delete {len(label_ids)} label{'' if sing else 's'}?"
            f"All annotations made with {'this' if sing else 'these'} "
            f"label{'' if sing else 's'} will be removed as well."
        )
        if not resp:
            return
        for label_id in label_ids:
            with self.connection:
                self.connection.execute(
                    "delete from label where id = ?", (label_id,)
                )
        self.event_generate("<<LabelsChanged>>")

    def total_n_docs(self, doc_filter="all docs"):
        if doc_filter == "labelled docs":
            return self.connection.execute(
                "select count(*) from (select distinct doc_id from annotation)"
            ).fetchone()[0]
        if doc_filter == "unlabelled docs":
            return self.connection.execute(
                "select count(*) from unlabelled_document "
            ).fetchone()[0]
        return self.connection.execute(
            "select count(*) from document"
        ).fetchone()[0]

    def get_docs(self, offset=0, page_size=10, doc_filter="all docs"):
        if doc_filter == "labelled docs":
            return self.connection.execute(
                "select id, substr(content, 1, 200) "
                "as trunc_content "
                "from labelled_document "
                "order by id limit ? offset ? ",
                (page_size, offset),
            ).fetchall()
        if doc_filter == "unlabelled docs":
            return self.connection.execute(
                "select id , substr(content, 1, 200) "
                "as trunc_content "
                "from unlabelled_document "
                "order by id limit ? offset ?",
                (page_size, offset),
            ).fetchall()
        return self.connection.execute(
            "select id, substr(content, 1, 200) as trunc_content "
            "from document order by id limit ? offset ? ",
            (
                page_size,
                offset,
            ),
        ).fetchall()

    def delete_docs(self, doc_ids):
        resp = tk.messagebox.askokcancel(
            message=f"Delete {len(doc_ids)} "
            f"document{'s' if len(doc_ids) > 1 else ''}?"
        )
        if not resp:
            return
        for doc_id in doc_ids:
            with self.connection:
                self.connection.execute(
                    "delete from document where id = ?", (doc_id,)
                )
        self.event_generate("<<DocumentsChanged>>")

    def delete_all_docs(self, *args):
        resp = tk.messagebox.askokcancel(message="Delete ALL documents?")
        if not resp:
            return
        with self.connection:
            self.connection.execute("delete from document")
        self.event_generate("<<DocumentsChanged>>")

    def import_labels(self, *args):
        n_before = self.connection.execute(
            "select count(*) from label"
        ).fetchone()[0]
        file_name = tk.filedialog.askopenfilename(
            filetypes=["{json files} {.json}", "{All files} {*}"]
        )
        if not file_name:
            return
        _database.add_labels_from_json(file_name)
        n_after = self.connection.execute(
            "select count(*) from label"
        ).fetchone()[0]
        n_imported = n_after - n_before
        self.event_generate("<<LabelsChanged>>")
        tk.messagebox.showinfo(message=f"Imported {n_imported} new labels")

    def import_documents(self, *args):
        n_before = self.connection.execute(
            "select count(*) from document"
        ).fetchone()[0]
        file_name = tk.filedialog.askopenfilename(
            filetypes=[
                "{csv files} {.csv}",
                "{Text files} {.txt}",
                "{All files} {*}",
            ]
        )
        if not file_name:
            return
        progress_display = _utils.centered_toplevel(self)
        tk.Label(
            progress_display, text="Importing documents ...", padx=30, pady=10
        ).grid(row=0, column=0, sticky="NEW")
        progress_bar = tk.ttk.Progressbar(
            progress_display, orient=tk.HORIZONTAL, mode="determinate"
        )
        progress_bar.grid(row=1, column=0, sticky="NSEW")
        _database.add_docs_from_file(file_name, progress_bar)
        progress_bar.destroy()
        progress_display.destroy()
        n_after = self.connection.execute(
            "select count(*) from document"
        ).fetchone()[0]
        n_imported = n_after - n_before
        self.event_generate("<<DocumentsChanged>>")
        tk.messagebox.showinfo(message=f"Imported {n_imported} new documents")

    def suggest_approver_name(self):
        default_name = getpass.getuser()
        return _database.get_app_state_extra("approver_name", default_name)

    def export_documents(self, labelled_only=True, approver_name=None):
        output_file = tk.filedialog.asksaveasfilename(
            filetypes=["{json files} {.json}", "{All files} {*}"]
        )
        if not output_file:
            return
        if approver_name:
            _database.set_app_state_extra("approver_name", approver_name)
        res = _database.export_annotations(
            output_file,
            labelled_docs_only=labelled_only,
            approver=approver_name,
        )
        n_docs, n_annotations = res["n_docs"], res["n_annotations"]
        tk.messagebox.showinfo(
            message=f"{n_annotations} annotations for {n_docs} docs "
            f"exported to {output_file}"
        )

    def set_label_color(self, label_id, new_color):
        if not new_color:
            return
        with self.connection:
            self.connection.execute(
                "update label set color = ? where id = ?",
                (new_color, label_id),
            )
        self.event_generate("<<LabelsChanged>>")
