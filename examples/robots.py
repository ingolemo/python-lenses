#!/usr/bin/env python3

import contextlib
import curses
import curses.textpad
from random import randint

from lenses import lens

MIN = 1
MAX = 20
ROBOTS = 6


@contextlib.contextmanager
def curses_context():
    '''a context manager for setting up curses'''
    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    screen.keypad(1)
    try:
        yield screen
    finally:
        screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()


def restrain(n):
    return max(MIN, min(n, MAX))


def cmp(a, b):
    return (a > b) - (a < b)


class GameState:

    def __init__(self):
        self.robots = set()
        self.crashes = set()
        self.player = (9, 9)
        self.running = True
        self.message = None

        for _ in range(ROBOTS):
            robot_coord = randint(MIN, MAX), randint(MIN, MAX)
            self.robots.add(robot_coord)

    def handle_input(self, input):
        dirs = {
            'h': (-1, 0), 'j': (0, 1), 'k': (0, -1), 'l': (1, 0),
            'y': (-1, -1), 'u': (1, -1), 'n': (1, 1), 'b': (-1, 1),
            '.': (0, 0),
        }

        if input in dirs:
            dx, dy = dirs[input]
            self = lens(self).player[0] + dx
            self = lens(self).player[1] + dy
            self = lens(self).player.both_().modify(restrain)
            return self, True
        elif input == 'q':
            return self.end_game(), False
        elif input == 't':
            self = lens(self).player.both_().modify(
                lambda a: randint(MIN, MAX))
            return self, True
        else:
            return self, False

    def advance_robots(self):
        new_robots = set()
        crashes = set(self.crashes)
        for x, y in self.robots:
            dx = cmp(self.player[0], x)
            dy = cmp(self.player[1], y)
            new_coord = (x + dx, y + dy)
            if new_coord in new_robots:
                crashes.add(new_coord)
                new_robots.remove(new_coord)
            elif new_coord in crashes:
                pass
            else:
                new_robots.add(new_coord)
        self = lens(self).robots.set(new_robots)
        self = lens(self).crashes.set(crashes)
        return self

    def check_game_end(self):
        if self.player in self.robots | self.crashes:
            return self.end_game('You Died!')
        elif not self.robots:
            return self.end_game('You Win!')
        else:
            return self

    def end_game(self, message=None):
        self = lens(self).message.set(message)
        return lens(self).running.set(False)

    def draw(self, screen):
        curses.textpad.rectangle(screen, MIN-1, MIN-1, MAX+1, MAX+1)
        for x in range(MIN, MAX + 1):
            for y in range(MIN, MAX + 1):
                coord = (x, y)
                if coord == self.player:
                    ch = b'@'
                elif coord in self.crashes:
                    ch = b'#'
                elif coord in self.robots:
                    ch = b'O'
                else:
                    ch = b'.'
                screen.addch(y, x, ch)


def main():
    with curses_context() as screen:
        state = GameState()
        state.draw(screen)
        while state.running:
            input = chr(screen.getch())

            state, should_advance = state.handle_input(input)
            if should_advance:
                state = state.advance_robots()
                state = state.check_game_end()

            screen.clear()
            state.draw(screen)
            screen.refresh()

        if state.message:
            screen.addstr(0, 2, state.message)
            screen.getch()


if __name__ == '__main__':
    main()
