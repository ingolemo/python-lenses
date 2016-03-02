#!/usr/bin/env python3

import sys
import tty
from random import randint

from lenses import lens

MIN = 1
MAX = 20
ROBOTS = 6


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

    def __str__(self):
        rows = []
        for y in range(MIN, MAX + 1):
            chars = []
            for x in range(MIN, MAX + 1):
                coord = (x, y)
                if coord == self.player:
                    ch = '@'
                elif coord in self.crashes:
                    ch = '#'
                elif coord in self.robots:
                    ch = 'O'
                else:
                    ch = '.'
                chars.append(ch)
            rows.append(''.join(chars))
        return '\n'.join(rows) + '\n'


def main():
    tty.setcbreak(sys.stdin.fileno())

    state = GameState()
    print(state)
    while state.running:
        input = sys.stdin.read(1)

        state, should_advance = state.handle_input(input)
        if should_advance:
            state = state.advance_robots()
            state = state.check_game_end()

        print(state)

    print(state.message)


if __name__ == '__main__':
    main()
