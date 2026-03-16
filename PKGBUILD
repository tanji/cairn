# Maintainer: Cairn contributors
pkgname=cairn
pkgver=1.0.0
pkgrel=1
pkgdesc="A simple GNOME task manager"
arch=('any')
url="https://github.com/cairn"
license=('MIT')
depends=(
    'python'
    'python-gobject'
    'gtk4'
    'libadwaita'
    'libnotify'
    'hicolor-icon-theme'
)
optdepends=(
    'libayatana-appindicator: system tray support'
)
makedepends=('meson' 'ninja')
source=("$pkgname-$pkgver.tar.gz::file:///home/guillaume/taskapp")  # placeholder; replace with real URL/tag
sha256sums=('SKIP')  # replace with real checksum for AUR

build() {
    cd "$srcdir/$pkgname-$pkgver"
    arch-meson build
    meson compile -C build
}

package() {
    cd "$srcdir/$pkgname-$pkgver"
    meson install -C build --destdir "$pkgdir"
}
