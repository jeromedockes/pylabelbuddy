import tkinter as tk
import tkinter.ttk
import tkinter.colorchooser

from pylabelbuddy._scrollable_list import ScrollableList


class DocumentsList(tk.Frame):
    def __init__(self, parent, dataset, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.dataset = dataset
        self.offset = 0
        self.page_size = 100
        self.docs = tk.StringVar()
        self.docs_list = ScrollableList(
            self, listbox_kwargs=dict(listvariable=self.docs)
        )
        self.delete_button = tk.Button(
            self.docs_list.buttons_frame,
            text="Delete",
            command=self.delete_selection,
        )
        self.delete_all_button = tk.Button(
            self.docs_list.buttons_frame,
            text="Delete ALL docs",
            command=self.dataset.delete_all_docs,
        )
        self.annotate_button = tk.Button(
            self.docs_list.buttons_frame,
            text="Annotate selected doc",
            command=self.go_to_annotations,
        )

        self.doc_filter_frame = tk.Frame(self.docs_list.buttons_frame)
        self.doc_filter = tk.StringVar(value="All docs")
        self.doc_filter.trace("w", self._filter_change)
        for i, val in enumerate(
            ["All docs", "Labelled docs", "Unlabelled docs"]
        ):
            button = tk.Radiobutton(
                self.doc_filter_frame,
                text=val,
                variable=self.doc_filter,
                value=val,
            )
            button.grid(row=1, column=i)
        self.paging_frame = tk.Frame(self.docs_list.buttons_frame)
        self.prev_button = tk.Button(
            self.paging_frame, text="<", command=self.prev_page
        )
        self.first_button = tk.Button(
            self.paging_frame, text="<<", command=self.first_page
        )
        self.paging_msg = tk.StringVar()
        self.paging_label = tk.Label(self.paging_frame)
        self.paging_label["textvariable"] = self.paging_msg
        self.next_button = tk.Button(
            self.paging_frame, text=">", command=self.next_page
        )
        self.last_button = tk.Button(
            self.paging_frame, text=">>", command=self.last_page
        )
        self.dataset.bind("<<DocumentsChanged>>", self.fill, add=True)
        self.dataset.bind("<<LabelsChanged>>", self.fill, add=True)
        self.docs_list.listbox.bind(
            "<<ListboxSelect>>", self._update_selection_button_states, add=True
        )

        self.first_button.grid(row=0, column=0)
        self.prev_button.grid(row=0, column=1)
        self.paging_label.grid(row=0, column=2)
        self.next_button.grid(row=0, column=3)
        self.last_button.grid(row=0, column=4)

        self.delete_button.grid(row=0, column=1)
        self.delete_all_button.grid(row=0, column=2)
        self.annotate_button.grid(row=0, column=3)

        self.doc_filter_frame.grid(row=1, columnspan=4, column=0, sticky="EW")

        self.paging_frame.grid(row=2, columnspan=4, column=0, sticky="EW")
        self.docs_list.grid(row=0, column=0, sticky="NSEW")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.fill()

    def _filter_change(self, *args):
        self.offset = 0
        self.fill()

    def _update_selection_button_states(self, *args):
        selection = self.docs_list.listbox.curselection()
        if selection:
            self.delete_button["state"] = "normal"
            self.annotate_button["state"] = "normal"
        else:
            self.delete_button["state"] = "disabled"
            self.annotate_button["state"] = "disabled"

    def _update_button_states(self, start, end, total):
        if start == 0:
            self.prev_button["state"] = "disabled"
            self.first_button["state"] = "disabled"
        else:
            self.prev_button["state"] = "normal"
            self.first_button["state"] = "normal"
        if end == total:
            self.next_button["state"] = "disabled"
            self.last_button["state"] = "disabled"
        else:
            self.next_button["state"] = "normal"
            self.last_button["state"] = "normal"

    def fill(self, *args):
        if not self.dataset.total_n_docs("all docs"):
            if not hasattr(self, "empty_banner"):
                self.empty_banner = tk.Label(
                    self,
                    text="No documents in database.\n\n"
                    "Go to Import / Export\nto import documents",
                )
                self.empty_banner.grid(column=0, row=0, sticky="NSWE")
                return
            else:
                self.empty_banner.lift()
        else:
            if hasattr(self, "empty_banner"):
                self.empty_banner.lower()
        total = self.dataset.total_n_docs(self.doc_filter.get().lower())
        self.offset = max(0, min(total - 1, self.offset))
        self.offset = self.offset - self.offset % self.page_size
        self.docs_info = self.dataset.get_docs(
            self.offset,
            page_size=self.page_size,
            doc_filter=self.doc_filter.get().lower(),
        )
        self.docs.set([row["trunc_content"] for row in self.docs_info])
        start, end = self.offset, self.offset + len(self.docs_info)
        if total:
            if start == end - 1:
                self.paging_msg.set(f"{end} / {total}")
            else:
                self.paging_msg.set(f"{start + 1} - {end} / {total}")
        else:
            self.paging_msg.set("0 / 0")
        self._update_button_states(start, end, total)
        self._update_selection_button_states(start, end, total)

    def next_page(self, *args):
        total_docs = self.dataset.total_n_docs(self.doc_filter.get().lower())
        if self.offset + self.page_size >= total_docs:
            return
        self.offset += self.page_size
        self.fill()

    def last_page(self, *args):
        total_docs = self.dataset.total_n_docs(self.doc_filter.get().lower())
        self.offset = total_docs - total_docs % self.page_size
        self.fill()

    def prev_page(self, *args):
        if self.offset == 0:
            return
        self.offset = max(0, self.offset - self.page_size)
        self.fill()

    def first_page(self, *args):
        if self.offset == 0:
            return
        self.offset = 0
        self.fill()

    def delete_selection(self, *args):
        selection = self.docs_list.listbox.curselection()
        selection = set(selection)
        selected_ids = [
            row["id"] for i, row in enumerate(self.docs_info) if i in selection
        ]
        self.dataset.delete_docs(selected_ids)

    def go_to_annotations(self, *args):
        selection = self.docs_list.listbox.curselection()
        if not selection:
            return
        first_selected = selection[0]
        self.requested_doc_id = self.docs_info[first_selected]["id"]
        self.event_generate("<<AnnotateRequest>>")


class LabelsList(tk.Frame):
    def __init__(self, parent, dataset, *args, use_colors=True, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.dataset = dataset
        self.use_colors = use_colors
        self.labels = tk.StringVar()
        self.labels_list = ScrollableList(
            self,
            listbox_kwargs=dict(listvariable=self.labels),
            scrollbar_side="left",
        )
        self.delete_button = tk.Button(
            self.labels_list.buttons_frame,
            text="Delete",
            command=self.delete_selection,
        )
        self.set_color_button = tk.Button(
            self.labels_list.buttons_frame,
            text="Set color",
            command=self._set_color_for_selection,
        )
        self.dataset.bind("<<LabelsChanged>>", self.fill, add=True)
        self.labels_list.listbox.bind(
            "<<ListboxSelect>>", self._update_button_states, add=True
        )
        self.delete_button.grid(row=0, column=1)
        self.set_color_button.grid(row=0, column=2)
        self.labels_list.grid(row=0, column=0, sticky="NSEW")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.fill()

    def _update_button_states(self, *args):
        selection = self.labels_list.listbox.curselection()
        if selection:
            self.delete_button["state"] = "normal"
            self.set_color_button["state"] = "normal"
        else:
            self.delete_button["state"] = "disabled"
            self.set_color_button["state"] = "disabled"

    def fill(self, *args):
        self.labels_info = self.dataset.get_labels()
        if not self.labels_info:
            if not hasattr(self, "empty_banner"):
                self.empty_banner = tk.Label(
                    self,
                    text="No labels in database.\n\n"
                    "Go to Import / Export\nto import labels",
                )
                self.empty_banner.grid(column=0, row=0, sticky="NSWE")
                return
            else:
                self.empty_banner.lift()
        else:
            if hasattr(self, "empty_banner"):
                self.empty_banner.lower()
        self.labels.set([row["string_form"] for row in self.labels_info])
        if self.use_colors:
            for i, row in enumerate(self.labels_info):
                self.labels_list.listbox.itemconfig(
                    i,
                    background=row["color"],
                    selectbackground="black",
                    selectforeground=row["color"],
                )
        self._update_button_states()

    def _get_selected_labels(self):
        selection = self.labels_list.listbox.curselection()
        selection = set(selection)
        return [
            row for i, row in enumerate(self.labels_info) if i in selection
        ]

    def _get_selected_ids(self):
        return [row["id"] for row in self._get_selected_labels()]

    def delete_selection(self, *args):
        self.dataset.delete_labels(self._get_selected_ids())

    def _set_color_for_selection(self, *args):
        selected_labels = self._get_selected_labels()
        if not selected_labels:
            return
        label = selected_labels[0]
        new_color = tk.colorchooser.askcolor(initialcolor=label["color"])
        if new_color:
            self.dataset.set_label_color(label["id"], new_color[1])


class DatasetMenu(tk.Frame):
    def __init__(self, parent, dataset, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.dataset = dataset
        self.panes = tk.ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.labels_list = LabelsList(self.panes, self.dataset)
        self.documents_list = DocumentsList(self.panes, self.dataset)
        self.panes.add(self.labels_list, weight=2)
        self.panes.add(self.documents_list, weight=4)
        self.panes.grid(sticky="NSEW")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
