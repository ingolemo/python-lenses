#!/usr/bin/env python3

'''
robots.py

You (`@`) are a person surrounded by killer robots (`O`). Dodge the
robots with the vi-keys (`hjkl`, `.` to wait, and `yubn` for diagonals)
and try to make them crash into each other. You win if all robots crash.
You lose if a robot lands on your square. If you find yourself stuck you
can press `t` to teleport to a new position. If you teleport next to a
robot then they will kill you, so watch out.
'''

import sys
import tty
from random import randint

from lenses import lens

MAXX = 40
MAXY = 20
ROBOTS = 12


def add_vectors(v1, v2):
    return (max(0, min(MAXX, v1[0] + v2[0])),
            max(0, min(MAXY, v1[1] + v2[1])))


def cmp(a, b):
    return (a > b) - (a < b)


def random_vector():
    return randint(0, MAXX), randint(0, MAXY)


class GameState:

    def __init__(self):
        self.robots = set()
        self.crashes = set()
        self.player = (MAXX // 2, MAXY // 2)
        self.running = True
        self.message = None

        for _ in range(ROBOTS):
            self.robots.add(random_vector())

    def handle_input(self, input):
        '''Takes a single character string as input and alters the game
        state according to that input. Mostly, this means moving the
        player around. Returns a new game state and boolean indicating
        whether the input had an effect on the state.'''

        dirs = {
            'h': (-1, 0), 'j': (0, 1), 'k': (0, -1), 'l': (1, 0),
            'y': (-1, -1), 'u': (1, -1), 'n': (1, 1), 'b': (-1, 1),
        }

        if input in dirs:
            new_pos = add_vectors(self.player, dirs[input])
            if new_pos == self.player:
                return self, False
            self = lens(self).player.set(new_pos)
            return self, True
        elif input == '.':
            return self, True
        elif input == 'q':
            return self.end_game(), False
        elif input == 't':
            self = lens(self).player.set(random_vector())
            return self, True
        else:
            return self, False

    def advance_robots(self):
        '''Produces a new game state in which the robots have advanced
        towards the player by one step. Handles the robots crashing into
        one another too.'''

        new_robots = set()
        crashes = set(self.crashes)
        for old_pos in self.robots:
            new_pos = add_vectors(
                old_pos, tuple(map(cmp, self.player, old_pos)))
            if new_pos in new_robots:
                crashes.add(new_pos)
                new_robots.remove(new_pos)
            elif new_pos in crashes:
                pass
            else:
                new_robots.add(new_pos)
        self = lens(self).robots.set(new_robots)
        self = lens(self).crashes.set(crashes)
        return self

    def check_game_end(self):
        '''Checks for the game's win/lose conditions and 'alters' the
        game state to reflect the condition found. If the game has not
        been won or lost then it just returns the game state
        unaltered.'''

        if self.player in self.robots | self.crashes:
            return self.end_game('You Died!')
        elif not self.robots:
            return self.end_game('You Win!')
        else:
            return self

    def end_game(self, message=''):
        '''Returns a completed game state object, setting an optional
        message to display after the game is over.'''

        self = lens(self).message.set(message)
        return lens(self).running.set(False)

    def __str__(self):
        rows = []
        for y in range(0, MAXY + 1):
            chars = []
            for x in range(0, MAXX + 1):
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
    '''The main function. Instantiates a GameState object and then
    enters a REPL-like main loop, waiting for input, updating the state
    based on the input, then outputting the new state.'''

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
