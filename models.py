"""GObject model for task list binding."""

from gi.repository import GObject
import database


class TaskObject(GObject.Object):
    __gtype_name__ = "TaskObject"

    def __init__(self, row):
        super().__init__()
        self._id = row["id"]
        self._name = row["name"]
        self._project = row["project"]
        self._deadline = row["deadline"]
        self._reminder = bool(row["reminder"])
        self._completed = bool(row["completed"])
        self._created_at = row["created_at"]
        self._completed_at = row["completed_at"]
        self._reminder_interval_hours = row["reminder_interval_hours"]  # int or None
        self._reminder_active_days = row["reminder_active_days"]        # str or None
        self._reminder_hour = row["reminder_hour"]                      # int or None
        self._reminder_minute = row["reminder_minute"]                  # int or None

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def project(self):
        return self._project

    @property
    def deadline(self):
        return self._deadline

    @property
    def reminder(self):
        return self._reminder

    @property
    def completed(self):
        return self._completed

    @property
    def created_at(self):
        return self._created_at

    @property
    def completed_at(self):
        return self._completed_at

    @property
    def reminder_interval_hours(self):
        return self._reminder_interval_hours

    @property
    def reminder_active_days(self):
        return self._reminder_active_days

    @property
    def reminder_hour(self):
        return self._reminder_hour

    @property
    def reminder_minute(self):
        return self._reminder_minute


def task_store_from_db(completed: bool = False):
    """Return a Gio.ListStore populated from the database."""
    from gi.repository import Gio

    store = Gio.ListStore.new(TaskObject)
    rows = database.get_completed_tasks() if completed else database.get_active_tasks()
    for row in rows:
        store.append(TaskObject(row))
    return store
