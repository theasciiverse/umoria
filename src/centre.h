// Asciiverse: show Umoria's 80x24 screen centred in a bigger terminal.
//
// After New BSD Games' src/centre.h (CC0), as theasciiverse/netbsd-games
// uses it for rogue and hunt (compat/centre.h, nb_fixed()). Included by
// curses.h after the curses header, so ui_io.cpp, the only file that talks
// to curses, works unchanged: initscr() swaps stdscr for a pad of 24x80,
// every drawing call lands on it at the game's own positions, refresh()
// shows the pad centred in the terminal and getch() follows a resized
// terminal. A terminal smaller than 80x24 shows the top left part.
//
// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

WINDOW *av_initscr();
int av_refresh();
int av_getch();

#undef initscr
#define initscr() av_initscr()
#undef refresh
#define refresh() av_refresh()
#undef getch
#define getch() av_getch()
