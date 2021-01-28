import tkinter as tk
import tkinter.scrolledtext


class SearchBox(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.search_string = tk.StringVar()
        self.entry_box = tk.Entry(self, textvariable=self.search_string)
        self.next_button = tk.Button(self, text="Next")
        self.prev_button = tk.Button(self, text="Prev")
        self.entry_box.pack(side="left")
        self.next_button.pack(side="left")
        self.prev_button.pack(side="left")


class SearchableText(tk.Frame):
    def __init__(self, parent, content, *args, found_tag="sel", **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.found_tag = found_tag
        self.text = tk.scrolledtext.ScrolledText(self, wrap="word")
        # self.text.bind("<Key>", lambda e: "break")
        self.text["state"] = "disabled"
        if self.found_tag != "sel":
            self.text.tag_configure(self.found_tag, background="yellow")
        self.search_box = SearchBox(self)

        self.search_box.search_string.trace("w", self._start_search)
        self.search_box.next_button.configure(command=self._search_next)
        self.search_box.prev_button.configure(command=self._search_prev)
        self.text.bind("<Control-s>", self._focus_and_search)
        self.text.bind("<Control-f>", self._focus_and_search)
        self.text.bind("<slash>", self._focus_and_search)
        self.search_box.entry_box.bind("<Return>", self._search_next)
        self.search_box.entry_box.bind("<Shift-Return>", self._search_prev)

        self.text.grid(row=0, column=0, sticky="NSEW")
        self.search_box.grid(row=1, column=0, sticky="EW")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.text.mark_set("match", "1.0")

        self.search_box.entry_box.focus_set()
        self._fill(content)

    def _fill(self, content):
        if content is None:
            content = "No documents in database"
        self.text["state"] = "normal"
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.text["state"] = "disabled"
        self.text.mark_set("match", "1.0")

    def _search_next(self, *args):
        self.text.mark_set("match", "match + 1c")
        self._start_search()

    def _search_prev(self, *args):
        self.text.mark_set("match", "match - 1c")
        self._start_search(forward=False)

    def _start_search(self, forward=True, *args):
        self.event_generate("<<Searching>>")
        self.text.tag_remove(self.found_tag, "1.0", tk.END)
        if forward:
            search_from = self.text.index("@0,0")
        else:
            search_from = self.text.index(
                f"@{self.winfo_width()},{self.winfo_height()}"
            )
        if forward and self.text.compare(search_from, "<=", "match"):
            search_from = "match"
        if (not forward) and self.text.compare(search_from, ">=", "match"):
            search_from = "match"
        pattern = self.search_box.search_string.get()
        if not pattern:
            return
        match_len = tk.IntVar()
        match = self.text.search(
            pattern,
            search_from,
            count=match_len,
            nocase=True,
            forwards=forward,
            backwards=(not forward)
        )
        if not match:
            return
        self.text.tag_add(
            self.found_tag, match, f"{match} + {match_len.get()} c"
        )
        self.text.see(match)
        self.text.mark_set("match", match)

    def _focus_and_search(self, *args):
        self.search_box.entry_box.focus_set()
        self._start_search()
