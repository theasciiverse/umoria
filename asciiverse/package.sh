#!/bin/sh
# Packs the build into dist/umoria-<target>.tar.gz (.zip for Windows) for
# av: the binary at the top, its read-only files beside it in data/ (av
# starts a title in its install folder, where umoria reads them), and
# LICENSE, AUTHORS and README.md. The player's own files are not in it:
# they live in the data folder (PATCHES.md).
#
#   asciiverse/package.sh x86_64-unknown-linux-musl
set -eu
cd "$(dirname "$0")/.."
target="$1"
case "$target" in *windows*) exe=.exe ;; *) exe= ;; esac
stage=stage/umoria
rm -rf "$stage" && mkdir -p "$stage/data" dist
cp "out/umoria$exe" LICENSE AUTHORS README.md "$stage/"
cp out/data/*.txt "$stage/data/"
if [ -n "$exe" ]; then
  (cd "$stage" && zip -qr "../../dist/umoria-$target.zip" .)
else
  tar -czf "dist/umoria-$target.tar.gz" -C "$stage" .
fi
ls dist
