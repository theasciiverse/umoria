# Changes from upstream

This is the Asciiverse packaging of [Umoria](https://github.com/dungeons-of-moria/umoria),
Robert A. Koeneke's Moria (1981 to 1986) in James E. Wilson's Unix
version (1987 to 1994), as restored by Michael R. Cook for 5.7
(GPL-3.0-or-later). Upstream is the `upstream` remote. The `asciiverse`
branch starts from upstream's `master` at
`3bf8abc4f76812810e59d738492c7b61fb8f1bb6` (2025-07-26), not the last
release, v5.7.15 (2021-06-02): the 37 commits after it fix a read out of
bounds, the lock picking skill, the character backgrounds table, a
startup crash and the build with clang 19, and add `-r` for roguelike
keys. They were never released, so the version stays 5.7.15. GitHub's
tarball of that commit has sha256
`5ec7480f789e5c9d435ff149dea0dd620e5b6d34f914deaa9b8ff5c1a2688eba`
and matches the commit's tree.

## Debian's patches

From moria 5.7.15-1 (`moria_5.7.15-1.debian.tar.xz`, sha256
`ca29edbfe313dee7a99bd899fce539c22f7066a89463a832a7ff1f1c20074932`);
Debian's packaging repo is the `debian` remote (salsa, `games-team/moria`).
Tagged `debian/5.7.15-1`.

- `dont-reopen-scores-file.patch`, applied unchanged (credited to Phil
  Brooke in Debian's changelog for 5.7.10+20181022-1): recording a score
  uses the score file opened at start instead of opening it a second
  time.
- Not applied: `set-scores-path.patch` and `set-data-path.patch` point the
  files at Debian's `/var/games` and `/usr/lib/games` (this packaging uses
  the player's data folder and the install folder instead, below);
  `remove-werror.patch` and `cross.patch` remove CMake lines upstream has
  since dropped itself.

## Code

- Files in the data folder. The score file and saved games were read
  and written in the folder the game was started in, which for an
  installed game is the install folder. They now live in `umoria/` under
  `$XDG_DATA_HOME` (else `~/.local/share`), or `%APPDATA%\umoria` on
  Windows, made on the first run with an empty score file, since the game
  will not start without one (`initializeDataFolder()` in
  `src/game_files.cpp`). A save or character sheet name without a folder
  in it goes there too; a SAVEGAME given on the command line is still
  found in the current folder first. Upstream's `data/scores.dat` holds a
  developer's test score and is not shipped. The game's own files
  (`data/`) are read from the folder it is started in, as before; av
  starts a title in its install folder.
- Player name. The default name came from `getlogin()` first; it now
  comes from `$LOGNAME` or `$USER` first, and is cut to fit the name
  field instead of copied past it.
- Centred. `src/centre.h` and `src/centre.cpp`, included through
  upstream's own `src/curses.h`: `stdscr` becomes a pad of 24x80, every
  drawing call lands on it unchanged, `refresh()` shows it centred in the
  terminal and `getch()` redraws it centred after a resize; between keys
  (running, resting) each refresh asks the terminal for its size. After
  New BSD Games' `src/centre.h` (CC0), as `theasciiverse/netbsd-games`
  uses it for rogue.
- Too small a terminal. On a terminal smaller than 80x24 the game printed
  its message while curses still had the terminal and quit without
  `endwin()`, so the message vanished with the alternate screen and the
  shell was left without echo. It now leaves curses first and says what
  size it needs.
- Closing the terminal. When the terminal closed mid-game, the end of
  input started the game's panic save, but the hangup signal arriving
  with it killed the game partway through writing `game.sav` (0 or 4096
  bytes in tests); the next start refused the file and quit until it was
  deleted by hand, so the character was lost. Umoria 5.7 has no signal
  handling, so `SIGHUP` is now ignored and the save completes; the game
  restores from it as before.

## Packaging (new files)

- `asciiverse/build.sh`, `asciiverse/package.sh`: build with upstream's
  CMake into `out/` (the binary and `data/`), and one archive per target
  with `data/`, LICENSE, AUTHORS and README.md. Static Linux names the
  static ncursesw (CMake's FindCurses looks only for shared libraries);
  Windows is cross-built with MinGW against PDCurses, laid out in
  `out/pdc` the way upstream's CMakeLists.txt expects the MinGW ncurses,
  so neither the sources nor CMakeLists.txt change for it.
- `.github/workflows/release.yml`: static Linux in Alpine (x86_64,
  aarch64), macOS (x86_64, arm64) and Windows x86_64 (MinGW and
  PDCurses), plus SHA256SUMS, on a tag.
- `asciiverse/record/`: the preview driver (`umoria.py`) and its
  recorder (`rec.py`, from netbsd-games', taught the SU and SD scrolls
  ncurses uses when the map moves to the next panel, which pyte lacks),
  which made `asciiverse/casts/umoria.cast`.

## Tested

Linux: native glibc, static musl (Alpine 3.22) and AddressSanitizer with
UndefinedBehaviorSanitizer builds, driven in a pseudo-terminal and read
through pyte: the splash, rolling a character, the town, the dungeon
(walking, fighting, picking things up, opening doors, stairs), the help
page, the character sheet, saving with ^X and restoring, quitting with
^K to the tombstone, a character sheet saved to a file and the score
table, closing the terminal mid-game and restoring, and resizing to
120x36 and to 79x24. No sanitizer reports. Windows: the MinGW + PDCurses
build run under Wine 10 (centred at 100x30, a character rolled, saved to
`%APPDATA%\umoria`). macOS: not built here.
