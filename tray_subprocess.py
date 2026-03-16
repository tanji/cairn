#!/usr/bin/env python3
"""Standalone GTK3 tray subprocess for AppIndicator3."""

import json
import sys
import threading

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")

from gi.repository import AyatanaAppIndicator3 as AppIndicator3
from gi.repository import GLib, Gtk


_indicator = None
_task_names: list[str] = []


def _send(msg: dict):
    try:
        print(json.dumps(msg), flush=True)
    except Exception:
        pass


def _build_menu(task_names: list[str]) -> Gtk.Menu:
    menu = Gtk.Menu()

    open_item = Gtk.MenuItem(label="Open Cairn")
    open_item.connect("activate", lambda *_: _send({"action": "show"}))
    menu.append(open_item)

    menu.append(Gtk.SeparatorMenuItem())

    if task_names:
        for name in task_names:
            item = Gtk.MenuItem(label=name)
            item.set_sensitive(False)
            menu.append(item)
        menu.append(Gtk.SeparatorMenuItem())

    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect("activate", lambda *_: (_send({"action": "quit"}), Gtk.main_quit()))
    menu.append(quit_item)

    menu.show_all()
    return menu


def _read_stdin():
    """Read JSON lines from stdin (sent by main process)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            if "task_count" in msg:
                count = msg["task_count"]
                names = msg.get("task_names", [])
                GLib.idle_add(_update_tasks, count, names)
        except json.JSONDecodeError:
            pass


def _update_tasks(count: int, names: list[str]):
    global _task_names, _indicator
    _task_names = names
    if _indicator:
        label = str(count) if count > 0 else ""
        _indicator.set_label(label, "")
        _indicator.set_menu(_build_menu(_task_names))
        if count == 0:
            title = "Cairn — no active tasks"
        elif count == 1:
            title = "Cairn — 1 active task"
        else:
            title = f"Cairn — {count} active tasks"
        _indicator.set_title(title)
    return GLib.SOURCE_REMOVE


def main():
    global _indicator

    _indicator = AppIndicator3.Indicator.new(
        "cairn",
        "checkbox-checked-symbolic",
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )
    _indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    _indicator.set_menu(_build_menu([]))
    _indicator.set_label("", "")

    # Read stdin in background thread
    t = threading.Thread(target=_read_stdin, daemon=True)
    t.start()

    Gtk.main()


if __name__ == "__main__":
    main()
