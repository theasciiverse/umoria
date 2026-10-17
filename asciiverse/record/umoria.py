"""Umoria preview: a Half-Troll warrior goes down into the mines of Moria
and fights what turns up.

Umoria's 80x24 screen is centred whole (src/centre.h), so in the 100x30
recording it starts at row 3, column 10; the map is the 66 columns right
of the status panel. The driver rolls a character (accepting the first
roll), walks across the town to the down staircase and takes it; in the
dungeon it attacks any monster beside it, rests when its hit points are
down to a third, walks over items to pick them up, opens doors and
explores towards the nearest unexplored edge, and once it has explored
for a while takes the next down staircase it sees. It answers -more-.
After about 50 seconds it saves and quits (^X), and the cast ends with
the terminal restored. A take where the hero dies early is recorded
again.

    python3 asciiverse/record/umoria.py

DEBUG=1 prints the screen at every step instead of recording quietly.
"""
import collections, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rec

OY, OX = 3, 10          # where the centred 80x24 screen sits in 100x30
MX = 13                 # the map starts at this column of the 80
ITEMS = set("!?$*|)[_-=\",~&{(/]")
FLOOR = set(".'>") | ITEMS
DIRS = {(1, -1): "1", (1, 0): "2", (1, 1): "3", (0, -1): "4",
        (0, 1): "6", (-1, -1): "7", (-1, 0): "8", (-1, 1): "9"}
DEBUG = os.environ.get("DEBUG")
LENGTH = 50


def grid(r):
    rows = r.rows()
    return [rows[OY + y][OX:OX + 80] for y in range(24)]


def on_map(y, x):
    return 1 <= y <= 22 and MX <= x < 80


def find(g, ch):
    for y in range(1, 23):
        x = g[y].find(ch, MX)
        if x >= 0:
            return y, x
    return None


def find_me(r, g):
    """The hero: the '@' under the cursor, where the game leaves it, else
    the first one on the map."""
    cy, cx = r.screen.cursor.y - OY, r.screen.cursor.x - OX
    if 1 <= cy <= 22 and MX <= cx < 80 and g[cy][cx] == "@":
        return cy, cx
    return find(g, "@")


def path_to(g, start, goal, walk):
    """First step of a shortest 8-way path to a cell where goal(y, x), and
    that cell."""
    seen = {start: None}
    q = collections.deque([start])
    while q:
        y, x = q.popleft()
        if (y, x) != start and goal(y, x):
            cell = (y, x)
            while seen[(y, x)] != start:
                y, x = seen[(y, x)]
            return (y - start[0], x - start[1]), cell
        for dy, dx in DIRS:
            ny, nx = y + dy, x + dx
            if on_map(ny, nx) and (ny, nx) not in seen and walk(ny, nx):
                seen[(ny, nx)] = (y, x)
                q.append((ny, nx))
    return None


def stat(g, name):
    for row in g:
        m = re.match(name + r" *: *(-?\d+)", row)
        if m:
            return int(m.group(1))
    return None


def dump(r):
    if DEBUG:
        print("\n".join(grid(r)), file=sys.stderr)
        print("-" * 80, file=sys.stderr)


def roll(r):
    """Roll a Half-Troll warrior called Ada and enter the town."""
    r.wait_for("press any key", 8)
    r.pump(1.5)
    r.key(" ", 0.6)          # the splash screen
    r.wait_for("Choose a race", 4)
    r.pump(0.8)
    r.key("h", 0.5)          # Half-Troll
    r.key("m", 0.6)          # male, then the rolled stats
    r.pump(1.2)
    r.key(rec.ESC, 0.6)      # accept them
    r.wait_for("Choose a class", 4)
    r.pump(0.6)
    r.key("a", 0.8)          # Warrior
    r.wait_for("name", 4)
    r.pump(0.4)
    for c in "Ada":
        r.key(c, 0.15)
    r.key(rec.ENTER, 1.4)
    r.key(" ", 0.8)          # the character sheet, then the town
    # a new character carries its kit unused: food, soft leather armour, a
    # cloak, a dagger and torches; wear and wield all but the food (each
    # leaves the next one as b)
    for _ in range(4):
        r.key("w", 0.35)
        r.key("b", 0.5)
        while "-more-" in grid(r)[0]:
            r.key(" ", 0.3)
    r.key("e", 1.6)          # show what is worn
    r.key(rec.ESC, 0.4)


def take():
    """One recording; True when the hero lived to the end."""
    out = os.environ.get("REC_OUT", os.path.join(rec.ROOT, "out"))
    r = rec.Rec("umoria", "Umoria", cwd=out)
    if DEBUG:
        send = r.key
        r.key = lambda k, wait=0.15: (print("key", repr(k), file=sys.stderr), send(k, wait))
    roll(r)
    visited = collections.Counter()
    depth_seen = 0.0
    last_level = None
    stairs_at = None        # the down staircase, also once we stand on it
    blocked = set()         # cells a step into did not move us (veins, rubble)
    last_move = None
    target = None           # the unexplored cell we are heading for
    tries = collections.Counter()   # attempts at opening each door
    seen = set()            # cells the torch has shown us
    fails = collections.Counter()   # steps that did not move us, by cell
    while r.elapsed() < LENGTH:
        g = grid(r)
        text = r.text()
        dump(r)
        if "RIP" in text or "killed by" in text:
            r.pump(1.0)
            r.finish(rec.ESC)
            print("the hero died early", file=sys.stderr)
            return False
        top = g[0]
        if "-more-" in top:
            r.key(" ", 0.15)
            continue
        if "[y/n]" in top or "(y/n)" in top or "?" in top and "help" not in top:
            r.key(rec.ESC, 0.15)
            continue
        level = g[23][60:].strip()
        if level != last_level:
            visited.clear()
            stairs_at = None
            blocked.clear()
            tries.clear()
            seen.clear()
            fails.clear()
            target = None
            last_move = None
            last_level = level
            depth_seen = r.elapsed()
        me = find_me(r, g)
        if me is None:
            r.key(rec.ESC, 0.2)
            continue
        if last_move and me not in last_move:
            # the map scrolled to the next panel: move what we know with it
            dy, dx = me[0] - last_move[1][0], me[1] - last_move[1][1]

            def moved(c):
                return (c[0] + dy, c[1] + dx) if c else c
            visited = collections.Counter({moved(c): n for c, n in visited.items()})
            seen = {moved(c) for c in seen}
            blocked = {moved(c) for c in blocked}
            tries = collections.Counter({moved(c): n for c, n in tries.items()})
            fails = collections.Counter({moved(c): n for c, n in fails.items()})
            target, stairs_at = moved(target), moved(stairs_at)
            last_move = (moved(last_move[0]), me)
        visited[me] += 1
        # the torch has lit every cell around us: walls stay on the map,
        # floor does not, so a blank cell seen this way is floor
        seen.update((me[0] + dy, me[1] + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1))
        y, x = me
        if last_move and last_move[0] == me:
            # a step that did not move us: twice, and that way is shut
            fails[last_move[1]] += 1
            if fails[last_move[1]] >= 2:
                blocked.add(last_move[1])
                target = None
        last_move = None
        if target == me:
            target = None
        # a monster next to us: hit it
        # (not a floating eye: its gaze paralyses whoever hits it)
        foe = next(((dy, dx) for (dy, dx) in DIRS
                    if on_map(y + dy, x + dx) and g[y + dy][x + dx].isalpha()
                    and g[y + dy][x + dx] != "e"), None)
        if foe:
            r.key(DIRS[foe], 0.16)
            continue
        hp, mhp = stat(g, "CHP"), stat(g, "MHP")
        in_town = "Town" in level
        in_sight = any(c.isalpha() for row in g[1:23] for c in row[MX:])
        # rest when hurt, but not in town or with a monster in sight,
        # which would only interrupt it
        if hp is not None and mhp and hp * 3 <= mhp and not in_town and not in_sight:
            r.key("R", 0.1)
            r.key("&", 0.05)
            r.key(rec.ENTER, 0.6)
            continue
        # a closed door beside us: open it
        door = next(((dy, dx) for (dy, dx) in DIRS
                     if on_map(y + dy, x + dx) and g[y + dy][x + dx] == "+"
                     and (y + dy, x + dx) not in blocked), None)
        if door:
            cell = (y + door[0], x + door[1])
            tries[cell] += 1
            if tries[cell] > 4:
                blocked.add(cell)   # locked or stuck: go another way
            r.key("o", 0.08)
            r.key(DIRS[door], 0.15)
            continue

        if in_town:
            def walk(fy, fx):
                return (fy, fx) not in blocked and (g[fy][fx] in ".>" or g[fy][fx] in ITEMS)
        else:
            # a dark corridor's floor is not remembered once the torch has
            # passed, so blank cells may be walked into too
            def walk(fy, fx):
                return (fy, fx) not in blocked and (g[fy][fx] in FLOOR or g[fy][fx] == " ")

        found = None
        stairs = find(g, ">")
        if stairs:
            stairs_at = stairs
        if stairs_at and (in_town or r.elapsed() - depth_seen > 22):
            if me == stairs_at:
                r.key(">", 0.6)
                continue
            found = path_to(g, me, lambda fy, fx: (fy, fx) == stairs_at, walk)

        def frontier(fy, fx):
            return g[fy][fx] == " " and (fy, fx) not in seen

        if found is None and not in_town:
            found = path_to(g, me, lambda fy, fx: g[fy][fx] in ITEMS, walk)
        if found is None and not in_town and target:
            # keep heading for the same unexplored cell, so the hero does
            # not dither between two
            found = path_to(g, me, lambda fy, fx: (fy, fx) == target, walk)
        if found is None and not in_town:
            found = path_to(g, me, frontier, walk)
            if found:
                target = found[1]
        if found is None and not in_town:
            found = path_to(g, me, lambda fy, fx: g[fy][fx] == "+" and (fy, fx) not in blocked,
                            lambda fy, fx: walk(fy, fx) or (g[fy][fx] == "+" and (fy, fx) not in blocked))
        if found is None:
            found = path_to(g, me, lambda fy, fx: visited[(fy, fx)] == 0, walk)
        if found is None:
            # nowhere left to go: try again what seemed shut, and look again
            # at what seemed explored
            blocked.clear()
            fails.clear()
            seen.clear()
            visited.clear()
            target = None
            r.key("5", 0.12)
            continue
        step = found[0]
        last_move = (me, (y + step[0], x + step[1]))
        if DEBUG:
            print("at", me, "step", step, "blocked", sorted(blocked), file=sys.stderr)
        r.key(DIRS[step], 0.06)
        # wait for the game to draw the move before judging it
        for _ in range(12):
            if find_me(r, grid(r)) != me:
                break
            r.pump(0.04)
    g = grid(r)
    fought = (stat(g, "EXP") or 0) >= 3 and "feet" in g[23]
    r.pump(1.0)
    r.key(b"\x18", 1.5)      # ^X: save and quit
    for _ in range(3):
        if r.pump(0.5) is False:
            break
        if "Rank" in r.text():
            r.pump(2.5)      # let the score table be seen
        r.key(" ", 0.6)
    r.finish(b"")
    if not fought:
        print("the hero met nothing to fight; recording again", file=sys.stderr)
    return fought


for attempt in range(8):
    if take():
        break
    print("not a good take; recording again", file=sys.stderr)
