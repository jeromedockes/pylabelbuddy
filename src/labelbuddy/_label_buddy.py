import sys
from pathlib import Path
import argparse
import tkinter as tk
import tkinter.scrolledtext
import tkinter.filedialog
import tkinter.messagebox

from labelbuddy import __version__
from labelbuddy import _database
from labelbuddy._annotations_notebook import AnnotationsNotebook
from labelbuddy._annotations_manager import AnnotationsManager
from labelbuddy._dataset_manager import DatasetManager


class LabelBuddy(tk.Tk):
    def __init__(self, db_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = db_path
        _database.set_db_path(db_path)

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
        self.title("labelbuddy")
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
        msg = f"labelbuddy version {__version__}\nBSD 3-Clause License"
        tk.messagebox.showinfo(message=msg)

    def _go_to_doc_in_browser(self):
        import webbrowser

        webbrowser.open("https://github.com/jeromedockes/labelbuddy")


def start_label_buddy(args=None):
    default_path = _database.get_default_db_path()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "database",
        nargs="?",
        type=str,
        default=None,
        help=f"Path to labelbuddy database. "
        f"If not provided, {default_path} will be used",
    )
    parser.add_argument(
        "--version", action="store_true", help="Print version and exit"
    )
    args = parser.parse_args(args)
    if args.version:
        print(f"labelbuddy version {__version__}")
        sys.exit(0)
    buddy = LabelBuddy(args.database)
    buddy.mainloop()
