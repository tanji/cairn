"""Settings/Preferences dialog."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk
import database
import reminders

_DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class SettingsDialog(Adw.PreferencesDialog):
    __gtype_name__ = "SettingsDialog"

    def __init__(self):
        super().__init__()
        self.set_title("Settings")

        page = Adw.PreferencesPage(title="General", icon_name="preferences-system-symbolic")
        self.add(page)

        # --- Start time group ---
        time_group = Adw.PreferencesGroup(
            title="First Reminder Time",
            description="The day's first (or only) reminder fires at this time.",
        )
        page.add(time_group)

        hour, minute = database.get_reminder_time()

        time_row = Adw.ActionRow(title="Start time")
        time_suffix = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        time_suffix.set_valign(Gtk.Align.CENTER)

        hour_adj = Gtk.Adjustment(value=hour, lower=0, upper=23, step_increment=1)
        self._hour_spin = Gtk.SpinButton(adjustment=hour_adj, digits=0)
        self._hour_spin.set_orientation(Gtk.Orientation.VERTICAL)
        self._hour_spin.set_wrap(True)
        self._hour_spin.connect("value-changed", self._on_time_changed)

        sep_label = Gtk.Label(label=":")
        sep_label.add_css_class("dim-label")

        minute_adj = Gtk.Adjustment(value=minute, lower=0, upper=59, step_increment=1)
        self._minute_spin = Gtk.SpinButton(adjustment=minute_adj, digits=0)
        self._minute_spin.set_orientation(Gtk.Orientation.VERTICAL)
        self._minute_spin.set_wrap(True)
        self._minute_spin.connect("value-changed", self._on_time_changed)

        time_suffix.append(self._hour_spin)
        time_suffix.append(sep_label)
        time_suffix.append(self._minute_spin)
        time_row.add_suffix(time_suffix)
        time_group.add(time_row)

        # --- Repeat group ---
        repeat_group = Adw.PreferencesGroup(
            title="Repeat Interval",
            description="Repeat reminders every N hours after the first. Set to 0 for once per day.",
        )
        page.add(repeat_group)

        interval = database.get_reminder_interval_hours()
        interval_adj = Gtk.Adjustment(value=interval, lower=0, upper=23, step_increment=1)
        self._interval_row = Adw.SpinRow(
            title="Every N hours",
            subtitle="0 = once per day",
            adjustment=interval_adj,
            digits=0,
        )
        self._interval_row.connect("notify::value", self._on_interval_changed)
        repeat_group.add(self._interval_row)

        # --- Active days group ---
        days_group = Adw.PreferencesGroup(
            title="Active Days",
            description="Reminders only fire on the selected days.",
        )
        page.add(days_group)

        active_days = database.get_reminder_active_days()

        days_row = Adw.ActionRow()
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        btn_box.set_valign(Gtk.Align.CENTER)

        self._day_buttons: list[Gtk.ToggleButton] = []
        for i, label in enumerate(_DAY_LABELS):
            btn = Gtk.ToggleButton(label=label)
            btn.set_active(i in active_days)
            btn.add_css_class("flat")
            btn.connect("toggled", self._on_day_toggled)
            btn_box.append(btn)
            self._day_buttons.append(btn)

        days_row.add_suffix(btn_box)
        days_row.set_activatable_widget(btn_box)
        days_group.add(days_row)

    def _on_time_changed(self, *_):
        hour = int(self._hour_spin.get_value())
        minute = int(self._minute_spin.get_value())
        database.set_setting("reminder_hour", str(hour))
        database.set_setting("reminder_minute", str(minute))
        reminders.reschedule()

    def _on_interval_changed(self, *_):
        interval = int(self._interval_row.get_value())
        database.set_setting("reminder_interval_hours", str(interval))
        reminders.reschedule()

    def _on_day_toggled(self, *_):
        active = [str(i) for i, btn in enumerate(self._day_buttons) if btn.get_active()]
        database.set_setting("reminder_active_days", ",".join(active))
        reminders.reschedule()
