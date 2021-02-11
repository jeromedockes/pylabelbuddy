import tkinter as tk

from pylabelbuddy._annotator import Annotator


class NavBar(tk.Frame):
    def __init__(self, parent, annotations_manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.annotations_manager = annotations_manager
        self.current_doc_msg = tk.StringVar()
        self.current_disp = tk.Label(self)
        self.current_disp["textvariable"] = self.current_doc_msg
        self.prev_button = tk.Button(
            self, text="Prev", command=self.annotations_manager.visit_prev
        )
        self.next_button = tk.Button(
            self, text="Next", command=self.annotations_manager.visit_next
        )
        self.prev_unlabelled_button = tk.Button(
            self,
            text="Prev unlabelled",
            command=self.annotations_manager.visit_prev_unlabelled,
        )
        self.next_unlabelled_button = tk.Button(
            self,
            text="Next unlabelled",
            command=self.annotations_manager.visit_next_unlabelled,
        )
        self.prev_labelled_button = tk.Button(
            self,
            text="Prev labelled",
            command=self.annotations_manager.visit_prev_labelled,
        )
        self.next_labelled_button = tk.Button(
            self,
            text="Next labelled",
            command=self.annotations_manager.visit_next_labelled,
        )
        self.prev_labelled_button.grid(row=0, column=1)
        self.prev_unlabelled_button.grid(row=0, column=2)
        self.prev_button.grid(row=0, column=3)
        self.current_disp.grid(row=0, column=4)
        self.next_button.grid(row=0, column=5)
        self.next_unlabelled_button.grid(row=0, column=6)
        self.next_labelled_button.grid(row=0, column=7)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(8, weight=1)
        self.update_position()

    def update_position(self):
        current_doc = self.annotations_manager.current_doc_position()
        first_doc = self.annotations_manager.first_doc()
        last_doc = self.annotations_manager.last_doc()
        first_unlabelled = self.annotations_manager.first_unlabelled()
        last_unlabelled = self.annotations_manager.last_unlabelled()
        first_labelled = self.annotations_manager.first_labelled()
        last_labelled = self.annotations_manager.last_labelled()
        n_docs = self.annotations_manager.n_docs()
        self.current_doc_msg.set(f"{current_doc + 1} / {n_docs}")
        doc_id = self.annotations_manager.current_doc_id
        if doc_id is None:
            return
        if first_doc == doc_id:
            self.prev_button["state"] = "disabled"
        else:
            self.prev_button["state"] = "normal"
        if last_doc == doc_id:
            self.next_button["state"] = "disabled"
        else:
            self.next_button["state"] = "normal"
        if first_unlabelled is None or first_unlabelled >= doc_id:
            self.prev_unlabelled_button["state"] = "disabled"
        else:
            self.prev_unlabelled_button["state"] = "normal"
        if last_unlabelled is None or last_unlabelled <= doc_id:
            self.next_unlabelled_button["state"] = "disabled"
        else:
            self.next_unlabelled_button["state"] = "normal"
        if first_labelled is None or first_labelled >= doc_id:
            self.prev_labelled_button["state"] = "disabled"
        else:
            self.prev_labelled_button["state"] = "normal"
        if last_labelled is None or last_labelled <= doc_id:
            self.next_labelled_button["state"] = "disabled"
        else:
            self.next_labelled_button["state"] = "normal"


class AnnotationsNavigator(tk.Frame):
    def __init__(self, parent, annotations_manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.annotations_manager = annotations_manager
        self.nav_bar = NavBar(self, self.annotations_manager)
        self.annotator = Annotator(self, self.annotations_manager)

        self.annotations_manager.bind(
            "<<VisitedDocChanged>>", self.refresh, add=True
        )
        self.nav_bar.grid(row=0, column=0, sticky="NEW")
        self.annotator.grid(row=1, column=0, sticky="NEWS")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.refresh()

    def refresh(self, *args):
        if self.annotations_manager.current_doc_id is None:
            if not hasattr(self, "no_docs_label"):
                self.no_docs_label = tk.Label(
                    self,
                    text="No documents in database\n\n"
                    "Go to Import / Export\nto import documents",
                )
                self.no_docs_label.grid(
                    column=0, row=0, rowspan=2, columnspan=2, sticky="NSWE"
                )
            else:
                self.no_docs_label.lift()
            return
        else:
            if hasattr(self, "no_docs_label"):
                self.no_docs_label.lower()
        self.nav_bar.update_position()
        self.annotator.refresh()
