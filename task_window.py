"""Main application window."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from datetime import date
from gi.repository import Adw, Gio, GLib, Gtk

import database
import reminders
from models import TaskObject
from task_editor import TaskEditorDialog
from settings_dialog import SettingsDialog
from exporter import export_history_to_csv


class TaskWindow(Adw.ApplicationWindow):
    __gtype_name__ = "TaskWindow"

    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Cairn")
        self.set_default_size(620, 680)
        self.set_startup_id("io.github.cairn")

        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        toolbar_view = Adw.ToolbarView()
        self._toast_overlay.set_child(toolbar_view)

        # Header bar
        header = Adw.HeaderBar()

        self._view_switcher_title = Adw.ViewSwitcherTitle()
        header.set_title_widget(self._view_switcher_title)

        # New task button
        new_btn = Gtk.Button(icon_name="list-add-symbolic")
        new_btn.set_tooltip_text("New Task (Ctrl+N)")
        new_btn.connect("clicked", self._on_new_task)
        header.pack_start(new_btn)

        # Hamburger menu
        menu = Gio.Menu()
        menu.append("Settings", "win.settings")
        menu.append("Preview Notifications", "win.preview-notifications")
        menu.append("Export History to CSV", "win.export-csv")
        menu.append("About", "win.about")

        menu_btn = Gtk.MenuButton(
            icon_name="open-menu-symbolic",
            menu_model=menu,
        )
        header.pack_end(menu_btn)
        toolbar_view.add_top_bar(header)

        # ViewStack
        self._stack = Adw.ViewStack()
        self._view_switcher_title.set_stack(self._stack)
        toolbar_view.set_content(self._stack)

        # ViewSwitcherBar at bottom for narrow windows
        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(self._stack)
        self._view_switcher_title.connect(
            "notify::title-visible",
            lambda t, *_: switcher_bar.set_reveal(t.get_title_visible()),
        )
        toolbar_view.add_bottom_bar(switcher_bar)

        # Tasks page
        tasks_scroll = Gtk.ScrolledWindow()
        tasks_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        tasks_page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self._tasks_status = Adw.StatusPage(
            title="No Tasks",
            description="Press + to add your first task.",
            icon_name="checkbox-checked-symbolic",
        )
        self._tasks_status.set_vexpand(True)

        self._tasks_clamp = Adw.Clamp()
        self._tasks_clamp.set_maximum_size(600)

        tasks_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tasks_list_box.set_margin_top(12)
        tasks_list_box.set_margin_bottom(12)
        tasks_list_box.set_margin_start(12)
        tasks_list_box.set_margin_end(12)

        self._tasks_listbox = Gtk.ListBox()
        self._tasks_listbox.add_css_class("boxed-list")
        self._tasks_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        tasks_list_box.append(self._tasks_listbox)

        self._tasks_clamp.set_child(tasks_list_box)
        tasks_page_box.append(self._tasks_status)
        tasks_page_box.append(self._tasks_clamp)
        tasks_scroll.set_child(tasks_page_box)

        self._stack.add_titled_with_icon(tasks_scroll, "tasks", "Tasks", "checkbox-checked-symbolic")

        # History page
        history_scroll = Gtk.ScrolledWindow()
        history_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        history_page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self._history_status = Adw.StatusPage(
            title="No Completed Tasks",
            description="Completed tasks will appear here.",
            icon_name="document-open-recent-symbolic",
        )
        self._history_status.set_vexpand(True)

        self._history_clamp = Adw.Clamp()
        self._history_clamp.set_maximum_size(600)

        history_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        history_list_box.set_margin_top(12)
        history_list_box.set_margin_bottom(12)
        history_list_box.set_margin_start(12)
        history_list_box.set_margin_end(12)

        self._history_listbox = Gtk.ListBox()
        self._history_listbox.add_css_class("boxed-list")
        self._history_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        history_list_box.append(self._history_listbox)

        self._history_clamp.set_child(history_list_box)
        history_page_box.append(self._history_status)
        history_page_box.append(self._history_clamp)
        history_scroll.set_child(history_page_box)

        self._stack.add_titled_with_icon(
            history_scroll, "history", "History", "document-open-recent-symbolic"
        )

        # Actions
        self._add_actions()

        # Keyboard shortcut
        app.set_accels_for_action("win.new-task", ["<Control>n"])

        # Initial load
        self.refresh()

    def _add_actions(self):
        new_task_action = Gio.SimpleAction.new("new-task", None)
        new_task_action.connect("activate", self._on_new_task)
        self.add_action(new_task_action)

        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self._on_settings)
        self.add_action(settings_action)

        preview_action = Gio.SimpleAction.new("preview-notifications", None)
        preview_action.connect("activate", lambda *_: reminders.fire_preview())
        self.add_action(preview_action)

        export_action = Gio.SimpleAction.new("export-csv", None)
        export_action.connect("activate", self._on_export_csv)
        self.add_action(export_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

    def refresh(self):
        """Reload both list boxes from the database."""
        self._populate_listbox(self._tasks_listbox, completed=False)
        self._populate_listbox(self._history_listbox, completed=True)

        has_tasks = self._tasks_listbox.get_first_child() is not None
        self._tasks_status.set_visible(not has_tasks)
        self._tasks_clamp.set_visible(has_tasks)

        has_history = self._history_listbox.get_first_child() is not None
        self._history_status.set_visible(not has_history)
        self._history_clamp.set_visible(has_history)

        # Update tray badge count via application
        app = self.get_application()
        if hasattr(app, "update_tray_count"):
            active_count = len(database.get_active_tasks())
            app.update_tray_count(active_count)

    def _populate_listbox(self, listbox: Gtk.ListBox, completed: bool):
        # Remove all existing rows
        child = listbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            listbox.remove(child)
            child = next_child

        rows = database.get_completed_tasks() if completed else database.get_active_tasks()
        for row in rows:
            task = TaskObject(row)
            list_row = self._make_task_row(task, completed)
            listbox.append(list_row)

    def _make_task_row(self, task: TaskObject, completed: bool) -> Adw.ActionRow:
        row = Adw.ActionRow()
        row.set_title(GLib.markup_escape_text(task.name))

        # Subtitle: project + deadline
        subtitle_parts = []
        if task.project:
            subtitle_parts.append(task.project)
        if task.deadline:
            subtitle_parts.append(f"Due: {task.deadline}")
        if subtitle_parts:
            row.set_subtitle(" · ".join(subtitle_parts))

        # Prefix: check button
        check = Gtk.CheckButton()
        check.set_active(completed)
        check.set_valign(Gtk.Align.CENTER)
        check.connect("toggled", self._on_check_toggled, task)
        row.add_prefix(check)

        # Suffix widgets
        if not completed:
            # Overdue label
            if task.deadline:
                try:
                    deadline_date = date.fromisoformat(task.deadline)
                    if deadline_date < date.today():
                        overdue_label = Gtk.Label(label="Overdue")
                        overdue_label.add_css_class("error")
                        overdue_label.set_valign(Gtk.Align.CENTER)
                        row.add_suffix(overdue_label)
                except ValueError:
                    pass

            # Reminder toggle button
            if task.reminder:
                reminder_btn = Gtk.Button(icon_name="alarm-symbolic")
                reminder_btn.set_tooltip_text("Reminder enabled — click to disable")
            else:
                reminder_btn = Gtk.Button(icon_name="appointment-missed-symbolic")
                reminder_btn.set_tooltip_text("Reminder disabled — click to enable")
            reminder_btn.add_css_class("flat")
            reminder_btn.set_valign(Gtk.Align.CENTER)
            reminder_btn.connect("clicked", self._on_toggle_reminder, task)
            row.add_suffix(reminder_btn)

            # Edit button
            edit_btn = Gtk.Button(icon_name="document-edit-symbolic")
            edit_btn.set_tooltip_text("Edit task")
            edit_btn.add_css_class("flat")
            edit_btn.set_valign(Gtk.Align.CENTER)
            edit_btn.connect("clicked", self._on_edit_task, task)
            row.add_suffix(edit_btn)

            # Delete button
            del_btn = Gtk.Button(icon_name="user-trash-symbolic")
            del_btn.set_tooltip_text("Delete task")
            del_btn.add_css_class("flat")
            del_btn.add_css_class("destructive-action")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.connect("clicked", self._on_delete_task, task)
            row.add_suffix(del_btn)

        return row

    def _on_check_toggled(self, check: Gtk.CheckButton, task: TaskObject):
        if check.get_active() and not task.completed:
            database.complete_task(task.id)
            self.refresh()
            self._show_toast(f'"{task.name}" completed')
        elif not check.get_active() and task.completed:
            database.uncomplete_task(task.id)
            self.refresh()

    def _on_toggle_reminder(self, btn, task: TaskObject):
        database.set_task_reminder(task.id, not task.reminder)
        self.refresh()

    def _on_new_task(self, *_):
        dialog = TaskEditorDialog()
        dialog.connect("task-saved", self._on_task_saved)
        dialog.present(self)

    def _on_edit_task(self, btn, task: TaskObject):
        dialog = TaskEditorDialog(task)
        dialog.connect("task-saved", self._on_task_saved)
        dialog.present(self)

    def _on_delete_task(self, btn, task: TaskObject):
        database.delete_task(task.id)
        self.refresh()
        self._show_toast(f'"{task.name}" deleted')

    def _on_task_saved(self, dialog, task_id: int):
        self.refresh()
        self._show_toast("Task saved")

    def _on_settings(self, *_):
        dlg = SettingsDialog()
        dlg.present(self)

    def _on_about(self, *_):
        about = Adw.AboutDialog(
            application_name="Cairn",
            version="1.0.0",
            developer_name="Guillaume Lefranc",
            developers=["Guillaume Lefranc (tanji) https://github.com/tanji"],
            license_type=Gtk.License.MIT_X11,
            comments="A simple GNOME task manager.",
            website="https://github.com/tanji/cairn",
            issue_url="https://github.com/tanji/cairn/issues",
            application_icon="io.github.cairn",
        )
        about.present(self)

    def _on_export_csv(self, *_):
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Export History to CSV")
        file_dialog.set_initial_name("task_history.csv")

        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(csv_filter)
        file_dialog.set_filters(filters)

        file_dialog.save(self, None, self._on_export_csv_done)

    def _on_export_csv_done(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file:
                rows = database.get_completed_tasks()
                count = export_history_to_csv(rows, file.get_path())
                self._show_toast(f"Exported {count} tasks to CSV")
        except GLib.Error as e:
            if e.code != 2:  # 2 = dismissed
                self._show_toast("Export failed")

    def _show_toast(self, message: str):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self._toast_overlay.add_toast(toast)
