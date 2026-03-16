#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version>  (e.g. $0 0.11.0)"
    exit 1
fi

VERSION="$1"
TAG="v$VERSION"

# Ensure working tree is clean
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: working tree has uncommitted changes. Commit or stash first."
    exit 1
fi

echo "Bumping version to $VERSION..."

sed -i "s/^pkgver=.*/pkgver=$VERSION/" PKGBUILD
sed -i "s/project('cairn', version: '[^']*'/project('cairn', version: '$VERSION'/" meson.build
sed -i "s/version=\"[^\"]*\"/version=\"$VERSION\"/" task_window.py
sed -i "s/<release version=\"[^\"]*\"/<release version=\"$VERSION\"/" io.github.cairn.metainfo.xml

echo "Updating PKGBUILD checksum..."
updpkgsums

git add PKGBUILD meson.build task_window.py io.github.cairn.metainfo.xml
git commit -m "chore: bump version to $VERSION"

echo "Tagging $TAG..."
git tag "$TAG"

echo "Pushing..."
git push origin master
git push origin "$TAG"

echo "Done. Released $TAG."
