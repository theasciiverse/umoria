// Asciiverse: the centring behind centre.h.
//
// SPDX-License-Identifier: GPL-3.0-or-later

#include "curses.h"

#ifndef _WIN32
#include <sys/ioctl.h>
#include <unistd.h>
#endif

// the real calls here
#undef initscr
#undef refresh
#undef getch

static constexpr int SCREEN_LINES = 24;
static constexpr int SCREEN_COLS = 80;

static WINDOW *pad = nullptr; // where the game draws
static int shown_y = -1;      // where it is shown, for which terminal size
static int shown_x = -1;
static int shown_lines = 0;
static int shown_cols = 0;

WINDOW *av_initscr() {
    if (pad == nullptr) {
        if (initscr() == nullptr) {
            return nullptr;
        }
        pad = newpad(SCREEN_LINES, SCREEN_COLS);
        if (pad != nullptr) {
            // no scrolling of screen regions: the picture moves by rewriting
            idlok(pad, FALSE);
            idlok(curscr, FALSE);
            // keypad, raw and the like are set on stdscr afterwards
            stdscr = pad;
        }
    }
    return stdscr;
}

// follow a resized terminal, also between keys (while running or resting)
static void checkSize() {
#ifdef TIOCGWINSZ
    struct winsize ws {};

    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0 && ws.ws_row > 0 && ws.ws_col > 0 && (ws.ws_row != LINES || ws.ws_col != COLS)) {
        resize_term(ws.ws_row, ws.ws_col);
    }
#endif
    stdscr = pad;
}

int av_refresh() {
    if (pad == nullptr) {
        return wrefresh(stdscr);
    }
    checkSize();

    int y = LINES > SCREEN_LINES ? (LINES - SCREEN_LINES) / 2 : 0;
    int x = COLS > SCREEN_COLS ? (COLS - SCREEN_COLS) / 2 : 0;
    if (y != shown_y || x != shown_x || LINES != shown_lines || COLS != shown_cols) {
        // the picture moved: blank the old place
        WINDOW *screen = newwin(0, 0, 0, 0);
        if (screen != nullptr) {
            wnoutrefresh(screen);
            delwin(screen);
        }
        shown_y = y;
        shown_x = x;
        shown_lines = LINES;
        shown_cols = COLS;
    }

    int h = SCREEN_LINES < LINES ? SCREEN_LINES : LINES;
    int w = SCREEN_COLS < COLS ? SCREEN_COLS : COLS;
    pnoutrefresh(pad, 0, 0, y, x, y + h - 1, x + w - 1);
    int result = doupdate();
    stdscr = pad;
    return result;
}

int av_getch() {
    if (pad == nullptr) {
        return wgetch(stdscr);
    }
    av_refresh(); // wgetch does not refresh a pad by itself

    int ch;
    while ((ch = wgetch(pad)) == KEY_RESIZE) {
#ifdef PDCURSES
        resize_term(0, 0);
#endif
        stdscr = pad;
        av_refresh();
    }
    stdscr = pad;
    return ch;
}
