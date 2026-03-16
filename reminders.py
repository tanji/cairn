"""Reminder scheduler using GLib timers and libnotify."""

from datetime import date, datetime, timedelta

import gi
gi.require_version("Notify", "0.7")

from gi.repository import GLib, Notify

import database

_timer_id: int | None = None
# Set of (date, task_id, slot_index) tuples that have already fired today.
_fired: set[tuple[date, int, int]] = set()


def _fire_slots_for_day(start_hour: int, start_minute: int, interval_hours: int) -> list[datetime]:
    """Return all datetime fire slots for today given start time and interval."""
    today = date.today()
    base = datetime(today.year, today.month, today.day, start_hour, start_minute)
    if interval_hours <= 0:
        return [base]
    slots = []
    t = base
    while t.date() == today:
        slots.append(t)
        t += timedelta(hours=interval_hours)
    return slots


def _parse_active_days(raw: str) -> set[int]:
    return {int(d) for d in raw.split(",") if d.strip().isdigit()}


def _check_reminders() -> bool:
    now = datetime.now()
    today = now.date()

    # Purge fired entries from previous days
    stale = {key for key in _fired if key[0] != today}
    _fired.difference_update(stale)

    global_start_hour, global_start_minute = database.get_reminder_time()
    global_interval = database.get_reminder_interval_hours()
    global_active_days = database.get_reminder_active_days()

    tasks_to_fire = []
    for task in database.get_reminder_tasks():
        # Resolve active days for this task
        if task["reminder_active_days"] is not None:
            active_days = _parse_active_days(task["reminder_active_days"])
        else:
            active_days = global_active_days

        if now.weekday() not in active_days:
            continue

        # Resolve start time for this task
        start_hour = task["reminder_hour"] if task["reminder_hour"] is not None else global_start_hour
        start_minute = task["reminder_minute"] if task["reminder_minute"] is not None else global_start_minute

        # Resolve interval for this task
        interval = task["reminder_interval_hours"] if task["reminder_interval_hours"] is not None else global_interval

        slots = _fire_slots_for_day(start_hour, start_minute, interval)

        for idx, slot in enumerate(slots):
            key = (today, task["id"], idx)
            if key in _fired:
                continue
            if slot <= now < slot + timedelta(minutes=2):
                _fired.add(key)
                tasks_to_fire.append(task)
                break  # one slot match per task per tick

    if tasks_to_fire:
        _fire_notifications(tasks_to_fire)

    return GLib.SOURCE_CONTINUE


def _fire_notifications(tasks) -> None:
    try:
        if not Notify.is_initted():
            Notify.init("Cairn")

        if len(tasks) == 1:
            task = tasks[0]
            body = task["project"] if task["project"] else ""
            if task["deadline"]:
                body = (body + f"\nDeadline: {task['deadline']}").strip()
            n = Notify.Notification.new(task["name"], body or None, "task-due")
        else:
            names = "\n".join(f"• {t['name']}" for t in tasks)
            n = Notify.Notification.new(
                f"{len(tasks)} tasks due today",
                names,
                "task-due",
            )
        n.set_urgency(Notify.Urgency.CRITICAL)
        n.show()
    except Exception as e:
        print(f"[reminders] notification error: {e}")


def start() -> None:
    global _timer_id
    if _timer_id is not None:
        GLib.source_remove(_timer_id)
    _timer_id = GLib.timeout_add_seconds(60, _check_reminders)


def reschedule() -> None:
    _fired.clear()
    start()
