import tkinter as tk
import tkinter.font
from pylabelbuddy._searchable_text import SearchableText
from pylabelbuddy._scrollable_frame import ScrollableFrame


class LabelChoices(tk.Frame):
    def __init__(self, parent, annotations_manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.label_buttons = []
        self.annotations_manager = annotations_manager
        self.delete_button = tk.Button(self, text="Delete")
        self.buttons_frame = ScrollableFrame(self)
        self.delete_button.grid(row=0, column=0, sticky="NEW")
        self.buttons_frame.grid(row=1, column=0, sticky="NSWE")
        self.grid_rowconfigure(1, weight=1)
        self.selected_label = tk.StringVar(value="")
        self._label_colors = None
        self.refresh()

    def refresh(self, *args):
        label_colors = self.annotations_manager.label_colors.items()
        if not label_colors:
            if not hasattr(self, "empty_banner"):
                self.empty_banner = tk.Label(
                    self,
                    text="No labels in database.\n\n"
                    "Go to Import / Export\nto import labels",
                )
                self.empty_banner.grid(
                    column=0, row=0, rowspan=2, sticky="NSWE"
                )
                return
            else:
                self.empty_banner.lift()
        else:
            if hasattr(self, "empty_banner"):
                self.empty_banner.lower()
        if label_colors == self._label_colors:
            self._disable_choices()
            return
        self._label_colors = label_colors
        for button in self.label_buttons:
            button.destroy()
        self.label_buttons = []
        for i, (label, color) in enumerate(self._label_colors):
            button = tk.Radiobutton(
                self.buttons_frame.inner_frame,
                text=label,
                variable=self.selected_label,
                value=label,
                background=color,
                activebackground=color,
            )
            button.grid(row=(i + 1), column=0, sticky="W")
            self.label_buttons.append(button)
        self._disable_choices()

    def _disable_choices(self, *args):
        for button in self.label_buttons:
            button["state"] = "disabled"

    def _enable_choices(self, *args):
        for button in self.label_buttons:
            button["state"] = "normal"

    def _disable_delete(self, *args):
        self.delete_button["state"] = "disabled"

    def _enable_delete(self, *args):
        self.delete_button["state"] = "normal"


class Annotator(tk.Frame):
    def __init__(self, parent, annotations_manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.annotations_manager = annotations_manager
        self.labelled_regions = {}
        self.active_labelled_region = None

        self.label_choices = LabelChoices(self, self.annotations_manager)
        self.text = SearchableText(self, self.annotations_manager.content)

        self.text.text.bind("<Button-1>", self._deactivate_region)
        self.text.bind("<<Searching>>", self._deactivate_region)
        self.text.text.bind("<<Selection>>", self._set_selection_button_states, add=True)
        self.label_choices.selected_label.trace(
            "w", self._set_label_for_selection
        )
        self.label_choices.delete_button.configure(
            command=self._delete_active_region
        )
        self.label_choices._disable_choices()
        self.label_choices._disable_delete()

        self.label_choices.grid(row=0, column=0, sticky="NSW")
        self.text.grid(row=0, column=1, sticky="WENS")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._load_existing_regions()

    def refresh(self, *args):
        self.label_choices.refresh()
        self.labelled_regions = {}
        self._deactivate_region()
        self.text._fill(self.annotations_manager.content)
        self._load_existing_regions()

    def _delete_region(self, region_id):
        info = self.labelled_regions[region_id]
        self.text.text.tag_remove(region_id, info["start"], info["end"])
        self.annotations_manager.delete_annotation(region_id)
        del self.labelled_regions[region_id]

    def _delete_active_region(self):
        if self.active_labelled_region is None:
            return
        active = self.active_labelled_region
        self._deactivate_region()
        self._delete_region(active)

    def _crop_labelled_regions(self, crop_start, crop_end):
        all_regions = list(self.labelled_regions.items())
        for region_id, region_info in all_regions:
            if self.text.text.compare(
                crop_start, "<", region_info["end"]
            ) and self.text.text.compare(region_info["start"], "<", crop_end):
                self._delete_region(region_id)

    def _create_region_tag(self, region_id, label, start, end):
        self.labelled_regions[region_id] = {
            "label": label,
            "start": start,
            "end": end,
        }
        self.text.text.tag_configure(
            region_id, background=self.annotations_manager.label_colors[label]
        )
        self.text.text.tag_add(region_id, start, end)
        self.text.text.tag_lower(region_id, "sel")
        self.text.text.tag_bind(
            region_id, "<ButtonRelease-1>", self._activate_region
        )

    def _load_existing_regions(self):
        annotations = self.annotations_manager.existing_regions()
        for region_id, label, char_start, char_end in annotations:
            region_id = str(region_id)
            start = self.text.text.index(f"1.0 + {char_start} c")
            end = self.text.text.index(f"1.0 + {char_end} c")
            self._create_region_tag(region_id, label, start, end)

    def _add_region(self, start, end, label):
        char_start = (self.text.text.count("1.0", start) or [0])[0]
        char_end = (self.text.text.count("1.0", end) or [0])[0]
        region_id = self.annotations_manager.add_annotation(
            label, char_start, char_end
        )
        if region_id is None:
            return
        region_id = str(region_id)
        self._create_region_tag(region_id, label, start, end)
        return region_id

    def _deactivate_region(self, *args):
        if not self.active_labelled_region:
            return
        self.text.text.tag_configure(
            self.active_labelled_region,
            relief=tk.FLAT,
            font=self.text.text.cget("font"),
            borderwidth=1,
        )
        self.active_labelled_region = None
        self.label_choices.selected_label.set("")
        self._set_selection_button_states()

    def _set_selection_button_states(self, *args):
        if self.active_labelled_region:
            self.label_choices._enable_choices()
            self.label_choices._enable_delete()
            return
        self.label_choices._disable_delete()
        if self.text.text.tag_ranges("sel"):
            self.label_choices._enable_choices()
            return
        self.label_choices._disable_choices()
        return

    def _activate_region(self, event):
        if self.text.text.tag_ranges("sel"):
            return
        idx = self.text.text.index(f"@{event.x},{event.y}")
        tags = self.text.text.tag_names(idx)
        for tag in tags:
            if tag in self.labelled_regions:
                self._set_active_region(tag)

    def _set_active_region(self, region_id):
        self.active_labelled_region = region_id
        info = self.labelled_regions[region_id]
        self.label_choices.selected_label.set(info["label"])
        self.text.text.tag_configure(
            region_id,
            relief=tk.RAISED,
            borderwidth=4,
            font="BuddySelectedFont",
        )
        self._set_selection_button_states()

    def _update_region_label(self, region_id, label):
        if self.labelled_regions[region_id]["label"] == label:
            return
        self.annotations_manager.update_annotation_label(region_id, label)
        self.labelled_regions[region_id]["label"] = label
        self.text.text.tag_configure(
            region_id, background=self.annotations_manager.label_colors[label]
        )

    def _set_label_for_selection(self, *args):
        label = self.label_choices.selected_label.get()
        if not label:
            return
        if self.active_labelled_region is not None:
            self._update_region_label(self.active_labelled_region, label)
            return
        ranges = self.text.text.tag_ranges("sel")
        if not ranges:
            return
        self.text.text.tag_remove("sel", "1.0", tk.END)
        start, end = map(self.text.text.index, ranges)
        self._crop_labelled_regions(start, end)
        region_id = self._add_region(start, end, label)
        self._set_active_region(region_id)
