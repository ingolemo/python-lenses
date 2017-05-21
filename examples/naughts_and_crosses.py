#!/usr/bin/env python3

'''
naughts_and_crosses.py

Play a game of naughts and crosses (also known as tic-tac-toe) against
the computer.  To make a move choose a cell and type the number and
letter of that cell. Your input must be exactly two characters long;
do not include any spacing or punctionation.
'''

import random
import enum

from lenses import lens


class Outcome(enum.Enum):
    'The possible outcomes of a game of naughts and crosses.'
    win_for_crosses = enum.auto()
    win_for_naughts = enum.auto()
    draw = enum.auto()
    ongoing = enum.auto()

    def __bool__(self):
        'Returns whether the game has concluded.'
        return self is not Outcome.ongoing

    def __str__(self):
        return {
            Outcome.win_for_crosses: 'X is the winner!',
            Outcome.win_for_naughts: 'O is the winner!',
            Outcome.draw: 'The game is a draw!',
        }.get(self, 'The winner is unknown.')


class Board:
    'A noughts and crosses board.'

    def __init__(self):
        self.board = ((' ',) * 3,) * 3

    def make_move(self, x, y):
        '''Return a board with a cell filled in by the current player. If
        the cell is already occupied then return the board unchanged.'''
        if self.board[y][x] == ' ':
            return lens(self).board[y][x].set(self.player)
        return self

    @property
    def player(self):
        'The player whose turn it currently is.'
        return 'X' if self._count('X') <= self._count('O') else 'O'

    @property
    def winner(self):
        'The winner of this board if one exists.'
        for potential_win in self._potential_wins():
            if potential_win == tuple('XXX'):
                return Outcome.win_for_crosses
            elif potential_win == tuple('OOO'):
                return Outcome.win_for_naughts
        if self._count(' ') == 0:
            return Outcome.draw
        return Outcome.ongoing

    def _count(self, character):
        '''Counts the number of cells in the board that contain a
        particular character.'''
        return sum(cell == character for cell in self._all_cells())

    def _potential_wins(self):
        '''Generates all the combinations of board positions that need
        to be checked for a win.'''
        yield from self.board
        yield from zip(*self.board)
        yield self.board[0][0], self.board[1][1], self.board[2][2]
        yield self.board[0][2], self.board[1][1], self.board[2][0]

    def __str__(self):
        result = []
        for letter, row in zip('abc', self.board):
            result.append(letter + '  ' + (' │ '.join(row)))
        return '   1   2   3\n' + ('\n  ───┼───┼───\n'.join(result))

    _all_cells = lens().board.each_().each_().get_all()


def player_move(board):
    '''Shows the board to the player on the console and asks them to
    make a move.'''
    print(board, end='\n\n')
    x, y = input('Enter move (e.g. 2b): ')
    print()
    return int(x) - 1, ord(y) - ord('a')


def random_move(board):
    'Makes a random move on the board.'
    return random.choice(range(3)), random.choice(range(3))


def play():
    'Play a game of naughts and crosses against the computer.'
    ai = {'X': player_move, 'O': random_move}
    board = Board()
    while not board.winner:
        x, y = ai[board.player](board)
        board = board.make_move(x, y)
    print(board, end='\n\n')
    print(board.winner)

if __name__ == '__main__':
    play()
