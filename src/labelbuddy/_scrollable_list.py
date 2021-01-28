import tkinter as tk


class ScrollableList(tk.Frame):
    def __init__(
        self,
        parent,
        *args,
        scrollbar_side="right",
        listbox_kwargs={},
        **kwargs
    ):
        super().__init__(parent, *args, **kwargs)
        self.scrollbar_side = scrollbar_side
        listbox_kwargs.setdefault("selectmode", "extended")
        self.listbox = tk.Listbox(self, **listbox_kwargs)
        self.scrollbar = tk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.listbox.yview
        )
        self.listbox["yscrollcommand"] = self.scrollbar.set
        self.buttons_frame = tk.Frame(self, relief="flat")
        self.select_all_button = tk.Button(
            self.buttons_frame, text="Select all", command=self.select_all
        )

        self.select_all_button.grid(row=0, column=0)

        if self.scrollbar_side == "right":
            self.buttons_frame.grid(row=0, column=0, sticky="EW")
            self.listbox.grid(row=1, column=0, sticky="NSEW")
            self.scrollbar.grid(row=1, column=1, sticky="NS")
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=1)
        else:
            self.buttons_frame.grid(row=0, column=1, sticky="EW")
            self.listbox.grid(row=1, column=1, sticky="NSEW")
            self.scrollbar.grid(row=1, column=0, sticky="NS")
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(1, weight=1)

    def select_all(self, *args):
        self.listbox.selection_set(0, "end")
        self.listbox.event_generate("<<ListboxSelect>>")
