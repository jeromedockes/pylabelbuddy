import tkinter as tk


class ScrollableFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = tk.Canvas(self)
        self.scrollbar = tk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.canvas["yscrollcommand"] = self.scrollbar.set

        self.inner_frame = tk.Frame(self.canvas)
        self.inner_frame_id = self.canvas.create_window(
            (0, 0),
            window=self.inner_frame,
            anchor="nw",
        )

        self.inner_frame.bind("<Configure>", self._configure_inner_frame)
        self.canvas.bind("<Configure>", self._configure_canvas)

        self.scrollbar.grid(column=0, row=0, sticky="NS")
        self.canvas.grid(column=1, row=0, sticky="NSWE")
        self.grid_rowconfigure(0, weight=1)

    def _configure_inner_frame(self, event):
        size = (
            self.inner_frame.winfo_reqwidth(),
            self.inner_frame.winfo_reqheight(),
        )
        self.canvas.config(scrollregion="0 0 {} {}".format(*size))
        if self.inner_frame.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.config(width=self.inner_frame.winfo_reqwidth())

    def _configure_canvas(self, event):
        if self.inner_frame.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.itemconfigure(
                self.inner_frame_id, width=self.canvas.winfo_width()
            )
