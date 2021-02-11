import sys
from pathlib import Path
import argparse
import tkinter as tk
import tkinter.scrolledtext
import tkinter.filedialog
import tkinter.messagebox

from pylabelbuddy import __version__
from pylabelbuddy import _database
from pylabelbuddy._annotations_notebook import AnnotationsNotebook
from pylabelbuddy._annotations_manager import AnnotationsManager
from pylabelbuddy._dataset_manager import DatasetManager
from pylabelbuddy import _utils

_FONT_NAMES = [
    "BuddyTextFont",
    "BuddySelectedFont",
    "TkFixedFont",
    "TkDefaultFont",
    "TkTextFont",
    "TkMenuFont",
    "TkHeadingFont",
    "TkCaptionFont",
    "TkSmallCaptionFont",
    "TkIconFont",
    "TkTooltipFont",
]


class _FontSizeDialog(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_offset = _database.get_app_global_parameters().get(
            "font_size_offset", 0
        )
        title = tk.Label(self, text="Set font size")
        minus_button = tk.Button(self, text="-", command=self._decrease_font)
        plus_button = tk.Button(self, text="+", command=self._increase_font)
        close_button = tk.Button(
            self, text="Close", command=self.winfo_toplevel().destroy
        )
        title.grid(row=0, column=0, columnspan=2, sticky="NSEW")
        minus_button.grid(row=1, column=0, sticky="EWNS")
        plus_button.grid(row=1, column=1, sticky="EWNS")
        close_button.grid(row=2, column=0, columnspan=2, sticky="EWNS")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _increase_font(self):
        if self.base_offset > 30:
            return
        for font_name in _FONT_NAMES:
            font = tk.font.nametofont(font_name)
            size = min(100, int(font.actual()["size"] + 1))
            font.configure(size=size)
        self.base_offset += 1
        _database.set_app_global_parameter(
            "font_size_offset", self.base_offset
        )

    def _decrease_font(self):
        if self.base_offset < -4:
            return
        for font_name in _FONT_NAMES:
            font = tk.font.nametofont(font_name)
            size = max(3, int(font.actual()["size"] - 1))
            font.configure(size=size)
        self.base_offset -= 1
        _database.set_app_global_parameter(
            "font_size_offset", self.base_offset
        )


class LabelBuddy(tk.Tk):
    def __init__(self, db_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _database.set_db_path(db_path)
        self.db_path = _database.get_db_path()
        _database.set_app_global_parameter(
            "last_opened_database", str(db_path)
        )
        self._setup_fonts()
        self.dataset_manager = DatasetManager(self)
        self.annotations_manager = AnnotationsManager(self)
        self.notebook = AnnotationsNotebook(
            self, self.annotations_manager, self.dataset_manager
        )

        self.notebook.grid(sticky="NSEW")
        self.dataset_manager.grid()
        self.annotations_manager.grid()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        stored_geometry = _database.get_app_global_parameters().get(
            "main_window_geometry", None
        )
        if stored_geometry:
            self.geometry(stored_geometry)
        self.title("pylabelbuddy")
        icon_path = str(Path(__file__).parent.joinpath("_data", "LB.png"))
        try:
            self.icon = tk.PhotoImage(file=icon_path)
            self.tk.call("wm", "iconphoto", self._w, self.icon)
        except Exception:
            pass
        self._setup_menu()

        self.bind(
            "<<DatabaseChanged>>",
            self.dataset_manager.change_database,
            add=True,
        )
        self.bind(
            "<<DatabaseChanged>>",
            self.annotations_manager.change_database,
            add=True,
        )
        self.bind(
            "<<DatabaseChanged>>", self.notebook.change_database, add=True
        )

        self.protocol("WM_DELETE_WINDOW", self._store_geometry_and_close)

    def _store_geometry_and_close(self, *args):
        self._store_geometry()
        self.destroy()

    def _store_geometry(self, *args):
        _database.set_app_global_parameter(
            "main_window_geometry", self.geometry()
        )

    def _setup_fonts(self):
        self.fonts = {}
        text_font = tk.font.nametofont("TkTextFont")
        buddy_text = tk.font.Font(font=text_font, name="BuddyTextFont")
        has_deja = "DejaVu Serif" in tk.font.families()
        inc = 2 if has_deja else 4
        fam = "DejaVu Serif" if has_deja else "Times"
        buddy_text.config(family=fam, size=buddy_text.actual()["size"] + inc)
        self.fonts["BuddyTextFont"] = buddy_text
        selected_text = tk.font.Font(font=buddy_text, name="BuddySelectedFont")
        if has_deja:
            selected_text.config(slant="italic")
        self.fonts["BuddySelectedFont"] = selected_text

        base_offset = _database.get_app_global_parameters().get(
            "font_size_offset", 0
        )
        for font_name in _FONT_NAMES:
            font = tk.font.nametofont(font_name)
            size = min(100, int(font.actual()["size"] + base_offset))
            font.configure(size=size)

    def _setup_menu(self):
        self.option_add("*tearOff", tk.FALSE)
        menubar = tk.Menu(self)
        self["menu"] = menubar
        menu_file = tk.Menu(menubar)

        menubar.add_cascade(menu=menu_file, label="File")
        menu_file.add_command(label="New", command=self._open_new_database)
        menu_file.add_command(label="Open...", command=self._open_database)
        menu_file.add_command(label="Quit", command=self.destroy)

        menu_help = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_help, label="Help")
        menu_help.add_command(
            label="Documentation", command=self._go_to_doc_in_browser
        )
        menu_help.add_command(label="About", command=self._show_about_info)

        menu_pref = tk.Menu(menubar)
        menubar.add_cascade(menu=menu_pref, label="Settings")
        menu_pref.add_command(label="Font size", command=self._set_font)

    def _set_font(self):
        dialog = _utils.centered_toplevel(self, (0.2, 0.15))
        plus_minus = _FontSizeDialog(dialog)
        plus_minus.grid(row=0, column=0, sticky="NSEW")
        return dialog, plus_minus

    def _open_new_database(self):
        return self._open_database(False)

    def _open_database(self, must_exist=True):
        filetypes = [
            "{sqlite3 databases} {.sqlite3}",
            "{sqlite3 databases} {.sqlite}",
            "{sqlite3 databases} {.db}",
            "{All files} {*}",
        ]
        if must_exist:
            db_path = tk.filedialog.askopenfilename(filetypes=filetypes)
        else:
            db_path = tk.filedialog.asksaveasfilename(filetypes=filetypes)
        if not db_path:
            return
        _database.set_app_global_parameter(
            "last_opened_database", str(db_path)
        )
        self.db_path = db_path
        _database.set_db_path(db_path)
        self.event_generate("<<DatabaseChanged>>")

    def _show_about_info(self):
        msg = f"pylabelbuddy version {__version__}\nBSD 3-Clause License"
        tk.messagebox.showinfo(message=msg)

    def _go_to_doc_in_browser(self):
        import webbrowser

        webbrowser.open("https://github.com/jeromedockes/pylabelbuddy")


def start_label_buddy(args=None):
    default_path = _database.get_default_db_path()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "database",
        nargs="?",
        type=str,
        default=None,
        help=f"Path to pylabelbuddy database. "
        f"If not provided, {default_path} will be used",
    )
    parser.add_argument(
        "--version", action="store_true", help="Print version and exit"
    )
    args = parser.parse_args(args)
    if args.version:
        print(f"pylabelbuddy version {__version__}")
        sys.exit(0)
    buddy = LabelBuddy(args.database or default_path)
    buddy.mainloop()
