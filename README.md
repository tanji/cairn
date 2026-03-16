# Cairn

A simple GNOME task manager built with GTK4 and libadwaita.

## Features

- Create and manage tasks with optional deadlines and project grouping
- Per-task or global reminder schedules with configurable repeat intervals and active days
- Reminder notifications grouped by urgency: due today, this week, this month, and coming up
- System tray integration via AyatanaAppIndicator3 (optional)
- Task history with CSV export
- Searchable project picker

## Screenshots

_Coming soon._

## Installation

### Arch Linux (PKGBUILD)

```bash
git clone https://github.com/tanji/cairn
cd cairn
makepkg -si
```

### Flatpak

```bash
flatpak-builder --user --install --force-clean _build io.github.cairn.json
flatpak run io.github.cairn
```

### From source

```bash
git clone https://github.com/tanji/cairn
cd cairn
python main.py
```

#### Dependencies

- Python 3
- PyGObject (`python-gobject`)
- GTK4 (`gtk4`)
- libadwaita (`libadwaita`)
- libnotify (`libnotify`)

Optional:
- `libayatana-appindicator` — system tray support

## Building (meson)

```bash
meson setup --prefix=/usr _build
meson compile -C _build
meson install -C _build
```

## License

MIT — see [LICENSE](LICENSE).

## Author

Guillaume Lefranc (tanji) — <https://github.com/tanji>
