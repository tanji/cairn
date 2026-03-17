#!/usr/bin/env python3
"""Entry point for the Cairn GNOME application."""

import json
import os
import subprocess
import sys

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

import database
import reminders

APP_ID = "io.github.cairn"
APP_NAME = "Cairn"


class TaskApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._window = None
        self._tray_proc = None
        self._tray_watch_id = None

    def do_activate(self):
        if self._window:
            self._window.present()
            return

        # Register bundled icons only when running from the source tree.
        # When installed, GTK finds cairn via the standard hicolor path automatically.
        _icons_dir = os.path.join(os.path.dirname(__file__), "icons", "cairn-hicolor", "hicolor")
        if os.path.isdir(_icons_dir):
            icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            icon_theme.add_search_path(_icons_dir)

        Gtk.Window.set_default_icon_name(APP_ID)

        from task_window import TaskWindow

        self._window = TaskWindow(self)
        self._window.connect("close-request", self._on_window_close_request)
        self._window.present()

        reminders.start()
        self._start_tray()

    @staticmethod
    def _tray_available() -> bool:
        """Return True only if the AyatanaAppIndicator3 typelib is installed on disk."""
        import subprocess as _sp
        result = _sp.run(
            ["python3", "-c",
             "import gi; gi.require_version('AyatanaAppIndicator3', '0.1'); "
             "from gi.repository import AyatanaAppIndicator3"],
            capture_output=True,
        )
        return result.returncode == 0

    def _start_tray(self):
        if not self._tray_available():
            print("[main] Tray unavailable (AyatanaAppIndicator3 not found), skipping.")
            return
        tray_script = os.path.join(os.path.dirname(__file__), "tray_subprocess.py")
        if not os.path.exists(tray_script):
            return
        try:
            self._tray_proc = subprocess.Popen(
                [sys.executable, tray_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            # Watch stdout for messages from tray
            channel = GLib.IOChannel.unix_new(self._tray_proc.stdout.fileno())
            self._tray_watch_id = GLib.io_add_watch(
                channel,
                GLib.PRIORITY_DEFAULT,
                GLib.IOCondition.IN | GLib.IOCondition.HUP,
                self._on_tray_message,
            )
        except Exception as e:
            print(f"[main] Failed to start tray: {e}")

    def _on_tray_message(self, channel, condition):
        if condition & GLib.IOCondition.HUP:
            return GLib.SOURCE_REMOVE

        try:
            status, line, length, terminator = channel.read_line()
            if not line:
                return GLib.SOURCE_CONTINUE
            msg = json.loads(line.strip())
            action = msg.get("action")
            if action == "show":
                if self._window:
                    self._window.present()
            elif action == "quit":
                self._cleanup_tray()
                self.quit()
        except Exception as e:
            print(f"[main] Tray message error: {e}")

        return GLib.SOURCE_CONTINUE

    def update_tray_count(self, count: int):
        if self._tray_proc and self._tray_proc.stdin:
            try:
                tasks = database.get_active_tasks()
                names = [t["name"] for t in tasks]
                msg = json.dumps({"task_count": count, "task_names": names}) + "\n"
                self._tray_proc.stdin.write(msg.encode())
                self._tray_proc.stdin.flush()
            except Exception:
                pass

    def _on_window_close_request(self, window):
        if self._tray_proc:
            window.hide()
            return True  # suppress destroy
        return False  # no tray — let the window close and the app quit normally

    def _cleanup_tray(self):
        if self._tray_watch_id:
            GLib.source_remove(self._tray_watch_id)
            self._tray_watch_id = None
        if self._tray_proc:
            try:
                self._tray_proc.terminate()
                self._tray_proc.wait(timeout=2)
            except Exception:
                pass
            self._tray_proc = None

    def do_shutdown(self):
        self._cleanup_tray()
        Adw.Application.do_shutdown(self)


def main():
    GLib.set_prgname(APP_ID)
    GLib.set_application_name(APP_NAME)
    database.init_db()
    app = TaskApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
