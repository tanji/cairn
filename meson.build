project('cairn', version: '0.10.0', meson_version: '>= 0.62.0')

gnome = import('gnome')

# Python sources installed as data (no compilation step needed)
python_sources = files(
  'main.py',
  'task_window.py',
  'task_editor.py',
  'settings_dialog.py',
  'reminders.py',
  'database.py',
  'models.py',
  'exporter.py',
  'tray_subprocess.py',
)

install_data(
  python_sources,
  install_dir: get_option('datadir') / 'cairn',
)

# Wrapper script (generated from template so path matches install prefix)
cairn_script = configure_file(
  input: 'bin/cairn.in',
  output: 'cairn',
  configuration: {'datadir': get_option('prefix') / get_option('datadir')},
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

# Desktop entry
install_data(
  'data/io.github.cairn.desktop',
  install_dir: get_option('datadir') / 'applications',
)

# AppStream metadata
install_data(
  'io.github.cairn.metainfo.xml',
  install_dir: get_option('datadir') / 'metainfo',
)

# Icons
foreach size : ['16x16', '22x22', '24x24', '32x32', '48x48', '64x64', '96x96', '128x128', '256x256', '512x512']
  install_data(
    'icons/cairn-hicolor/hicolor' / size / 'apps/io.github.cairn.png',
    install_dir: get_option('datadir') / 'icons' / 'hicolor' / size / 'apps',
  )
endforeach

install_data(
  'icons/cairn-hicolor/hicolor/scalable/apps/io.github.cairn.svg',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps',
)

gnome.post_install(
  glib_compile_schemas: false,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
