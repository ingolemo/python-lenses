#!/usr/bin/env python3

import contextlib
import curses
from random import randrange

from lenses import lens

SIZE = 20
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
    return max(0, min(n, SIZE - 1))


def cmp(a, b):
    return -1 if a < b else 1 if a > b else 0


class GameState:

    def __init__(self):
        self.robots = set()
        self.crashes = set()
        self.player = (9, 9)
        self.running = True
        self.message = None

        for _ in range(ROBOTS):
            robot_coord = randrange(SIZE), randrange(SIZE)
            self.robots.add(robot_coord)

    def handle_input(self, input):
        dirs = {
            'h': (-1, 0), 'j': (0, 1), 'k': (0, -1), 'l': (1, 0),
            'y': (-1, -1), 'u': (1, -1), 'n': (1, 1), 'b': (-1, 1),
        }

        if input == 'q':
            return self.end_game(), False
        elif input == 't':
            return lens(self).player.both_().modify(
                lambda a: randrange(SIZE)), True
        elif input in dirs:
            dx, dy = dirs[input]
            self = lens(self).player[0] + dx
            self = lens(self).player[1] + dy
            self = lens(self).player.both_().modify(restrain)
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

        if self.player in new_robots | crashes:
            return self.end_game('You Died!')
        elif not new_robots:
            return self.end_game('You Win!')
        else:
            return self

    def end_game(self, message=None):
        self = lens(self).message.set(message)
        return lens(self).running.set(False)

    def draw(self, screen):
        for robot in self.robots:
            screen.addstr(robot[1], robot[0], 'O')
        for crash in self.crashes:
            screen.addstr(crash[1], crash[0], '*')
        screen.addstr(self.player[1], self.player[0], '@')


def main():
    with curses_context() as screen:
        state = GameState()
        state.draw(screen)
        while state.running:
            input = chr(screen.getch())

            state, should_advance = state.handle_input(input)
            if should_advance:
                state = state.advance_robots()

            screen.clear()
            state.draw(screen)
            screen.refresh()

        if state.message:
            screen.addstr(9, 4, state.message)
            screen.getch()


if __name__ == '__main__':
    main()
