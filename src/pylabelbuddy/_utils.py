import tkinter as tk


def centered_toplevel(widget, offset=(0.3, 0.3)):
    top = widget.winfo_toplevel()
    x, y = top.winfo_x(), top.winfo_y()
    w, h = top.winfo_width(), top.winfo_height()
    new_window = tk.Toplevel()
    new_window.geometry(f"+{x + int(w * offset[0])}+{y + int(h * offset[1])}")
    return new_window
