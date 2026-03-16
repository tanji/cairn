"""Task create/edit dialog."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, GObject, Gtk
from datetime import date

import database


class ProjectPickerRow(Adw.ActionRow):
    """An ActionRow that opens a popover for searching/creating/selecting a project."""

    __gtype_name__ = "ProjectPickerRow"

    def __init__(self):
        super().__init__(title="Project")
        self._selected: str = ""

        self._label = Gtk.Label(label="None")
        self._label.add_css_class("dim-label")
        self._label.set_valign(Gtk.Align.CENTER)
        self.add_suffix(self._label)

        chevron = Gtk.Image.new_from_icon_name("pan-end-symbolic")
        chevron.set_valign(Gtk.Align.CENTER)
        self.add_suffix(chevron)

        self.set_activatable(True)
        self.connect("activated", self._open_popover)

        self._popover = self._build_popover()
        self._popover.set_parent(self)

    def _build_popover(self) -> Gtk.Popover:
        popover = Gtk.Popover()
        popover.set_size_request(300, 320)
        popover.add_css_class("menu")

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer.set_margin_top(8)
        outer.set_margin_bottom(8)
        outer.set_margin_start(8)
        outer.set_margin_end(8)

        # Search entry
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search or create project…")
        self._search_entry.connect("search-changed", self._on_search_changed)
        self._search_entry.connect("activate", self._on_search_activate)
        outer.append(self._search_entry)

        # Scrolled list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list_box.add_css_class("boxed-list")
        self._list_box.connect("row-activated", self._on_row_activated)
        scroll.set_child(self._list_box)
        outer.append(scroll)

        # "Clear" row at the bottom
        clear_row = Gtk.ListBoxRow()
        clear_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        clear_box.set_margin_top(6)
        clear_box.set_margin_bottom(6)
        clear_box.set_margin_start(12)
        clear_box.set_margin_end(12)
        clear_icon = Gtk.Image.new_from_icon_name("edit-clear-symbolic")
        clear_lbl = Gtk.Label(label="No project")
        clear_lbl.add_css_class("dim-label")
        clear_box.append(clear_icon)
        clear_box.append(clear_lbl)
        clear_row.set_child(clear_box)
        self._list_box.append(clear_row)
        self._clear_row = clear_row

        popover.set_child(outer)
        return popover

    def _open_popover(self, *_):
        self._search_entry.set_text("")
        self._rebuild_list("")
        self._popover.popup()
        self._search_entry.grab_focus()

    def _rebuild_list(self, query: str):
        # Remove all rows except the persistent clear row
        row = self._list_box.get_first_child()
        while row:
            next_row = row.get_next_sibling()
            if row is not self._clear_row:
                self._list_box.remove(row)
            row = next_row

        projects = database.get_projects()
        q = query.strip().lower()
        matches = [p for p in projects if q in p.lower()] if q else projects

        for name in matches:
            self._list_box.prepend(self._make_project_row(name))

        # If the search text doesn't exactly match an existing project, show a
        # "Create <query>" row at the top.
        if q and q not in [p.lower() for p in projects]:
            create_row = Gtk.ListBoxRow()
            create_row._project_name = query.strip()
            create_row._is_create = True
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            box.set_margin_top(6)
            box.set_margin_bottom(6)
            box.set_margin_start(12)
            box.set_margin_end(12)
            icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
            lbl = Gtk.Label(label=f'Create "{query.strip()}"')
            box.append(icon)
            box.append(lbl)
            create_row.set_child(box)
            self._list_box.prepend(create_row)

    def _make_project_row(self, name: str) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row._project_name = name
        row._is_create = False
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(12)
        box.set_margin_end(12)

        lbl = Gtk.Label(label=name, xalign=0)
        lbl.set_hexpand(True)
        box.append(lbl)

        # Checkmark if currently selected
        if name == self._selected:
            check = Gtk.Image.new_from_icon_name("object-select-symbolic")
            box.append(check)

        # Delete button
        del_btn = Gtk.Button(icon_name="user-trash-symbolic")
        del_btn.add_css_class("flat")
        del_btn.add_css_class("destructive-action")
        del_btn.set_valign(Gtk.Align.CENTER)
        del_btn.connect("clicked", self._on_delete_project, name)
        box.append(del_btn)

        row.set_child(box)
        return row

    def _on_search_changed(self, entry):
        self._rebuild_list(entry.get_text())

    def _on_search_activate(self, entry):
        # Pick the topmost row (create or first match)
        first = self._list_box.get_first_child()
        if first and first is not self._clear_row:
            self._list_box.emit("row-activated", first)

    def _on_row_activated(self, listbox, row):
        if row is self._clear_row:
            self._select("")
            self._popover.popdown()
            return

        name = row._project_name
        if getattr(row, "_is_create", False):
            database.create_project(name)

        self._select(name)
        self._popover.popdown()

    def _on_delete_project(self, btn, name: str):
        database.delete_project(name)
        if self._selected == name:
            self._select("")
        self._rebuild_list(self._search_entry.get_text())

    def _select(self, name: str):
        self._selected = name
        self._label.set_text(name if name else "None")

    def get_project(self) -> str:
        return self._selected

    def set_project(self, name: str):
        self._select(name)


class TaskEditorDialog(Adw.Dialog):
    __gtype_name__ = "TaskEditorDialog"

    __gsignals__ = {
        "task-saved": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    def __init__(self, task=None):
        super().__init__()
        self._task = task
        self._deadline_date: date | None = None

        self.set_title("Edit Task" if task else "New Task")
        self.set_content_width(420)
        self.set_content_height(580)

        # Build content
        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        # Save button in header
        self._save_btn = Gtk.Button(label="Save")
        self._save_btn.add_css_class("suggested-action")
        self._save_btn.connect("clicked", self._on_save)
        header.pack_end(self._save_btn)

        # Cancel button
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda *_: self.close())
        header.pack_start(cancel_btn)

        # Scrolled content
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(500)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(12)
        box.set_margin_end(12)

        # Basic info group
        basic_group = Adw.PreferencesGroup()

        self._name_row = Adw.EntryRow(title="Task name")
        self._name_row.connect("notify::text", self._on_name_changed)
        basic_group.add(self._name_row)

        self._project_picker = ProjectPickerRow()
        basic_group.add(self._project_picker)

        box.append(basic_group)

        # Deadline group
        deadline_group = Adw.PreferencesGroup()

        self._deadline_expander = Adw.ExpanderRow(title="Deadline")
        self._deadline_expander.set_subtitle("No deadline set")
        self._deadline_expander.set_show_enable_switch(True)
        self._deadline_expander.connect("notify::enable-expansion", self._on_deadline_toggled)

        # Calendar inside expander
        cal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        cal_box.set_margin_top(8)
        cal_box.set_margin_bottom(8)
        cal_box.set_halign(Gtk.Align.CENTER)

        self._calendar = Gtk.Calendar()
        self._calendar.connect("day-selected", self._on_day_selected)
        cal_box.append(self._calendar)

        # Clear deadline button
        clear_btn = Gtk.Button(label="Clear deadline")
        clear_btn.set_margin_top(8)
        clear_btn.set_halign(Gtk.Align.CENTER)
        clear_btn.connect("clicked", self._on_clear_deadline)
        cal_box.append(clear_btn)

        self._deadline_expander.add_row(
            Adw.ActionRow(child=cal_box)
        )
        deadline_group.add(self._deadline_expander)
        box.append(deadline_group)

        # Reminder group
        reminder_group = Adw.PreferencesGroup()

        self._reminder_row = Adw.SwitchRow(title="Reminder", subtitle="Get notified at your reminder time")
        self._reminder_row.connect("notify::active", self._on_reminder_toggled)
        reminder_group.add(self._reminder_row)

        # Override expander — enable switch off by default
        self._override_expander = Adw.ExpanderRow(title="Custom schedule")
        self._override_expander.set_subtitle("Override global reminder settings for this task")
        self._override_expander.set_show_enable_switch(True)
        self._override_expander.set_enable_expansion(False)
        self._override_expander.set_sensitive(False)
        reminder_group.add(self._override_expander)

        # Hour / minute on one row
        time_row = Adw.ActionRow(title="Start time")
        time_suffix = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        time_suffix.set_valign(Gtk.Align.CENTER)

        hour_adj = Gtk.Adjustment(value=8, lower=0, upper=23, step_increment=1)
        self._override_hour_spin = Gtk.SpinButton(adjustment=hour_adj, digits=0)
        self._override_hour_spin.set_orientation(Gtk.Orientation.VERTICAL)
        self._override_hour_spin.set_wrap(True)

        sep_label = Gtk.Label(label=":")
        sep_label.add_css_class("dim-label")

        minute_adj = Gtk.Adjustment(value=0, lower=0, upper=59, step_increment=1)
        self._override_minute_spin = Gtk.SpinButton(adjustment=minute_adj, digits=0)
        self._override_minute_spin.set_orientation(Gtk.Orientation.VERTICAL)
        self._override_minute_spin.set_wrap(True)

        time_suffix.append(self._override_hour_spin)
        time_suffix.append(sep_label)
        time_suffix.append(self._override_minute_spin)
        time_row.add_suffix(time_suffix)
        self._override_expander.add_row(time_row)

        # Interval spin inside expander
        interval_adj = Gtk.Adjustment(value=0, lower=0, upper=23, step_increment=1)
        self._override_interval_row = Adw.SpinRow(
            title="Every N hours",
            subtitle="0 = once per day",
            adjustment=interval_adj,
            digits=0,
        )
        self._override_expander.add_row(self._override_interval_row)

        # Day toggles — label above, buttons below
        days_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        days_container.set_margin_top(8)
        days_container.set_margin_bottom(8)
        days_container.set_margin_start(12)
        days_container.set_margin_end(12)

        days_label = Gtk.Label(label="Active days", xalign=0)
        days_label.add_css_class("caption")
        days_label.add_css_class("dim-label")
        days_container.append(days_label)

        self._day_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        _DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self._override_day_buttons: list[Gtk.ToggleButton] = []
        for label in _DAY_LABELS:
            btn = Gtk.ToggleButton(label=label)
            btn.add_css_class("flat")
            self._day_btn_box.append(btn)
            self._override_day_buttons.append(btn)
        days_container.append(self._day_btn_box)

        days_row = Adw.ActionRow()
        days_row.set_child(days_container)
        self._override_expander.add_row(days_row)

        box.append(reminder_group)

        clamp.set_child(box)
        scroll.set_child(clamp)
        toolbar_view.set_content(scroll)
        self.set_child(toolbar_view)

        # Pre-populate if editing
        if task:
            self._name_row.set_text(task.name or "")
            if task.project:
                self._project_picker.set_project(task.project)
            self._reminder_row.set_active(task.reminder)
            self._override_expander.set_sensitive(task.reminder)
            has_override = any(x is not None for x in [
                task.reminder_interval_hours, task.reminder_active_days,
                task.reminder_hour, task.reminder_minute,
            ])
            if has_override:
                self._override_expander.set_enable_expansion(True)
                if task.reminder_hour is not None:
                    self._override_hour_spin.set_value(task.reminder_hour)
                if task.reminder_minute is not None:
                    self._override_minute_spin.set_value(task.reminder_minute)
                if task.reminder_interval_hours is not None:
                    self._override_interval_row.set_value(task.reminder_interval_hours)
                if task.reminder_active_days is not None:
                    active = {int(d) for d in task.reminder_active_days.split(",") if d.strip().isdigit()}
                    for i, btn in enumerate(self._override_day_buttons):
                        btn.set_active(i in active)
            if task.deadline:
                try:
                    d = date.fromisoformat(task.deadline)
                    self._deadline_date = d
                    self._deadline_expander.set_enable_expansion(True)
                    self._deadline_expander.set_expanded(True)
                    self._calendar.select_day(
                        GLib.DateTime.new_local(d.year, d.month, d.day, 0, 0, 0)
                    )
                    self._deadline_expander.set_subtitle(task.deadline)
                except ValueError:
                    pass

        self._update_save_sensitivity()

    def _set_default_day_buttons(self):
        """Set day toggles to Mon–Fri."""
        for i, btn in enumerate(self._override_day_buttons):
            btn.set_active(i < 5)

    def _on_reminder_toggled(self, row, *_):
        active = row.get_active()
        self._override_expander.set_sensitive(active)
        if not active:
            self._override_expander.set_enable_expansion(False)

    def _on_name_changed(self, *_):
        self._update_save_sensitivity()

    def _update_save_sensitivity(self):
        self._save_btn.set_sensitive(bool(self._name_row.get_text().strip()))

    def _on_deadline_toggled(self, row, *_):
        if not row.get_enable_expansion():
            self._deadline_date = None
            self._deadline_expander.set_subtitle("No deadline set")

    def _on_day_selected(self, calendar):
        dt = calendar.get_date()
        self._deadline_date = date(dt.get_year(), dt.get_month(), dt.get_day_of_month())
        self._deadline_expander.set_subtitle(self._deadline_date.isoformat())

    def _on_clear_deadline(self, *_):
        self._deadline_date = None
        self._deadline_expander.set_subtitle("No deadline set")
        self._deadline_expander.set_enable_expansion(False)

    def _on_save(self, *_):
        name = self._name_row.get_text().strip()
        project = self._project_picker.get_project()
        deadline = self._deadline_date.isoformat() if self._deadline_date else None
        reminder = self._reminder_row.get_active()

        # Collect override values — None means "use global"
        override_hour = override_minute = override_interval = override_days = None
        if reminder and self._override_expander.get_enable_expansion():
            override_hour = int(self._override_hour_spin.get_value())
            override_minute = int(self._override_minute_spin.get_value())
            override_interval = int(self._override_interval_row.get_value())
            active = [str(i) for i, btn in enumerate(self._override_day_buttons) if btn.get_active()]
            override_days = ",".join(active) if active else ""

        if self._task:
            database.update_task(
                self._task.id, name, project, deadline, reminder,
                override_interval, override_days, override_hour, override_minute,
            )
            task_id = self._task.id
        else:
            task_id = database.create_task(
                name, project, deadline, reminder,
                override_interval, override_days, override_hour, override_minute,
            )

        self.emit("task-saved", task_id)
        self.close()
