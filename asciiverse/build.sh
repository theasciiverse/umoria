#!/bin/sh
# Builds umoria into out/ with upstream's CMake: the binary as out/umoria
# and its read-only files in out/data/ (help pages, the welcome and death
# screens, and splash and version pages CMake fills in). The compiler,
# flags and curses library come from the environment, so one script serves
# every target (see .github/workflows/release.yml):
#
#   asciiverse/build.sh                                   # Linux, macOS
#   CURSES_LIB=/usr/lib/libncursesw.a LDFLAGS="-static -s" \
#     asciiverse/build.sh                                 # Alpine, static
#   CXXFLAGS="-arch arm64" LDFLAGS="-arch arm64" asciiverse/build.sh  # macOS
#   CXX=x86_64-w64-mingw32-g++-posix PDCURSES=/path/to/PDCurses-3.9 \
#     LDFLAGS=-s asciiverse/build.sh                      # Windows
#
# Umoria reads data/ from the folder it is started in, where av installs
# it, and keeps the player's files in the data folder (PATCHES.md).
set -eu
cd "$(dirname "$0")/.."
rm -rf out/build out/data out/pdc out/umoria out/umoria.exe
mkdir -p out
# Windows: upstream's CMake links the MinGW ncurses under /$MINGW and its
# curses.h includes <ncurses/ncurses.h> there. PDCurses (wincon, built with
# the same compiler) is laid out in out/pdc to look like that, so the
# sources and CMakeLists.txt need no change for it.
if [ -n "${PDCURSES:-}" ]; then
  p="$PWD/out/pdc"
  mkdir -p "$p/include/ncurses" "$p/lib"
  cp "$PDCURSES/curses.h" "$p/include/"
  printf '#include <curses.h>\n' > "$p/include/ncurses/ncurses.h"
  cp "$PDCURSES/wincon/pdcurses.a" "$p/lib/libncurses.a"
  export MINGW="${p#/}"
  CMAKE_ARGS="${CMAKE_ARGS:-} -DCMAKE_SYSTEM_NAME=Windows -DCMAKE_CXX_COMPILER=${CXX:-x86_64-w64-mingw32-g++}"
fi
# CMake's FindCurses only looks for shared libraries: CURSES_LIB names the
# static one to link instead
if [ -n "${CURSES_LIB:-}" ]; then
  CMAKE_ARGS="${CMAKE_ARGS:-} -DCURSES_NCURSES_LIBRARY=$CURSES_LIB -DCURSES_CURSES_LIBRARY=$CURSES_LIB"
  CMAKE_ARGS="$CMAKE_ARGS -DCURSES_EXTRA_LIBRARY=$CURSES_LIB -DCURSES_FORM_LIBRARY=$CURSES_LIB"
fi
cmake -S . -B out/build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS="${CXXFLAGS:-}" -DCMAKE_EXE_LINKER_FLAGS="${LDFLAGS:-}" \
  ${CMAKE_ARGS:-}
cmake --build out/build -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"
exe=
[ -f out/build/umoria/umoria.exe ] && exe=.exe
cp "out/build/umoria/umoria$exe" "out/umoria$exe"
mkdir -p out/data
cp out/build/umoria/data/*.txt out/data/
echo "built umoria$exe"
