# Maintainer: Cairn contributors
pkgname=cairn
pkgver=0.10.0
pkgrel=1
pkgdesc="A simple GNOME task manager"
arch=('any')
url="https://github.com/tanji/cairn"
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
source=("$pkgname-$pkgver.tar.gz::https://github.com/tanji/cairn/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('03f367e17783eac8dcd528ce20893874d06491d514d9d55c7e95d7af389e532d')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    arch-meson build
    meson compile -C build
}

package() {
    cd "$srcdir/$pkgname-$pkgver"
    meson install -C build --destdir "$pkgdir"
}
