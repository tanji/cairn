#!/bin/bash
set -e

PKGNAME="cairn"
TMPDIR="$(mktemp -d)"
AUR_REMOTE="ssh://aur@aur.archlinux.org/${PKGNAME}.git"

echo "Cloning AUR repo..."
git clone "$AUR_REMOTE" "$TMPDIR"
git -C "$TMPDIR" checkout -b master 2>/dev/null || git -C "$TMPDIR" checkout master

echo "Copying PKGBUILD..."
cp PKGBUILD "$TMPDIR/"

echo "Generating .SRCINFO..."
cd "$TMPDIR"
makepkg --printsrcinfo > .SRCINFO

echo "Committing..."
git add PKGBUILD .SRCINFO
git diff --cached --stat

PKGVER=$(grep '^pkgver=' PKGBUILD | cut -d= -f2)
PKGREL=$(grep '^pkgrel=' PKGBUILD | cut -d= -f2)
git commit -m "Update to ${PKGVER}-${PKGREL}"

echo "Pushing to AUR..."
git push origin master

echo "Done. https://aur.archlinux.org/packages/${PKGNAME}"

cd - > /dev/null
rm -rf "$TMPDIR"
