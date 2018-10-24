#!/usr/bin/env python3
import re

WHITE = 'w'
BLACK = 'b'
FIELD = ' '

CLI_BG = '\033[43m'
CLI_BOARD = '\033[90m'
CLI_WHITE = '\033[37m'
CLI_BLACK = '\033[30m'
CLI_BOLD = '\033[1m'
CLI_RED = '\033[91m'
CLI_RESET = '\033[0m'

class Chessman(object):
    def __init__(self, colour):
        self.colour = colour
        self.en_passante = False

    def __str__(self):
        return self.__class__.__name__.lower() if self.colour == BLACK else self.__class__.__name__

    def is_placeable(self, other):
        return other == FIELD or self.is_opponent(other)

    def is_opponent(self, other):
        return isinstance(other, Chessman) and other.colour != self.colour

    def __nearing(self, _from, _to):
        if _from == _to:
            return None
        step = 1 if _to > _from else -1
        it = _from
        while it != (_to-step):
            it += step
            yield it

    def is_move_allowed(self, fromy, fromx, san):
        self.dy = abs(san.y-fromy)
        self.dx = abs(san.x-fromx)
        self.ity = self.__nearing(fromy, san.y)
        self.itx = self.__nearing(fromx, san.x)
        if self.is_placeable(san.target):
            return self._is_move_allowed(fromy, fromx, san)
        return False

class K(Chessman):
    def _is_move_allowed(self, fromy, fromx, san):
        return self.dy < 2 and self.dx < 2

class R(Chessman):
    def _is_move_allowed(self, fromy, fromx, san):
        if (self.dy == 0) != (self.dx == 0):
            for x in self.itx:
                if board.get(x, fromy) != FIELD:
                    return False
            for y in self.ity:
                if board.get(fromx, y) != FIELD:
                    return False
            return True
        return False

class B(Chessman):
    def _is_move_allowed(self, fromy, fromx, san):
        if self.dy == self.dx:
            for x in self.itx:
                y = next(self.ity)
                if board.get(x, y) != FIELD:
                    return False
            return True
        return False

class Q(R, B):
    def _is_move_allowed(self, fromy, fromx, san):
        return R._is_move_allowed(self, fromy, fromx, san) or B._is_move_allowed(self, fromy, fromx, san)

class N(Chessman):
    def _is_move_allowed(self, fromy, fromx, san):
        return (self.dy == 2 and self.dx == 1) or (self.dy == 1 and self.dx == 2)

class P(Chessman):
    def is_move_allowed(self, fromy, fromx, san):
        self.dy = abs(san.y-fromy)
        self.dx = abs(san.x-fromx)
        self.en_passante = False

        # check direction
        if self.colour == WHITE and san.y-fromy not in range(1, 3 if fromy == 1 else 2):
            return False
        if self.colour == BLACK and fromy-san.y not in range(1, 3 if fromy == 6 else 2):
            return False

        # check capture
        if self.dx == 1 and self.dy == 1:
            passante = board.get(san.x, fromy)
            if isinstance(passante, san.piece_type) and self.is_opponent(passante):
                self.en_passante = True
            if self.is_opponent(san.target) or self.en_passante:
                return True

        # check straight move
        if self.dx == 0 and san.target == FIELD:
            # check if free double jump
            if self.dy == 2 and board.get(san.x, san.y-(1 if self.colour == WHITE else -1)) != FIELD:
                return False
            return True

        return False

class Board(object):
    file_to_idx = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    def __init__(self):
        self.winner = None
        self.board = [[FIELD for x in range(8)] for y in range(8)]
        for san in list(map(lambda y: San(y), 'Ra1 Nb1 Bc1 Qd1 Ke1 Bf1 Ng1 Rh1 a2 b2 c2 d2 e2 f2 g2 h2 Ra8 Nb8 Bc8 Qd8 Ke8 Bf8 Ng8 Rh8 a7 b7 c7 d7 e7 f7 g7 h7'.split())):
            chessman = san.piece_type(BLACK if san.y > 3 else WHITE)
            self.board[san.y][san.x] = chessman

    def move(self, colour, san):
        if san.special is not None:
            self.special(san.special)
        else:
            chessman = self.pop(colour, san)
            self.put(san, chessman)

    def put(self, san, chessman):
        if isinstance(self.get(san.x, san.y), K):
            self.winner = chessman.colour
        self.board[san.y][san.x] = chessman
        self.try_promote(san)

    def pop(self, colour, san):
        for idxR, rank in enumerate(self.board):
            for idxF, field in enumerate(rank):
                if isinstance(field, san.piece_type) and field.colour == colour and field.is_move_allowed(idxR, idxF, san):
                    self.board[idxR][idxF] = FIELD
                    if field.en_passante:
                        self.board[idxR][san.x] = FIELD
                    return field
        raise ValueError('Invalid move')

    def get(self, x, y):
        return self.board[y][x]

    def try_promote(self, san):
        if isinstance(san.target, P) and (san.y == 0 or san.y == 7):
            self.board[san.y][san.x] = Q(san.target.colour)

    def win(self, colour):
        self.winner = colour

    def special(self, sanspecial):
        if sanspecial == San.blackresigned:
            self.win(WHITE)
        if sanspecial == San.whiteresigned:
            self.win(BLACK)

    def __str__(self):
        res = '    a   b   c   d   e   f   g   h'
        idx = 8
        for rank in reversed(self.board):
            res += '\n  '
            res += cgi('+---+---+---+---+---+---+---+---+\n')
            res += str(idx)+' '
            res += cgi('| ')
            res += cgi(' | ').join(list(map(display_field, rank)))
            res += cgi(' |')
            res += ' '+str(idx)
            idx -= 1
        res += '\n  '
        res += cgi('+---+---+---+---+---+---+---+---+\n')
        res += '    a   b   c   d   e   f   g   h'
        return res

def display_field(field):
    if field == FIELD:
        return cgi(field)
    if field.colour == BLACK:
        return cgi(field, fg=CLI_BLACK)
    return cgi(field, fg=CLI_WHITE, fw=CLI_BOLD)

def cgi(text, fg=CLI_BOARD, bg=CLI_BG, fw=''):
    return '{}{}{}{}{}'.format(fg, fw, bg, text, CLI_RESET)

# standard algebraic notation
class San(object):
    file_to_idx = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    blackresigned = 'br'
    whiteresigned = 'wr'

    def __init__(self, notation):
        if not re.match(r'^([NBRQK])?([a-h])?([1-8])?(x)?([a-h][1-8])(=[NBRQK])?(\+|#)?$|^O-O(-O)?$|^1-0$|^0-1$', notation):
            raise ValueError('{} is not a valid SAN expression'.format(notation))
        self.notation = notation
        self.special = None
        self.checkresigned()

    @property
    def piece_type(self):
        return globals()[self.notation[0] if self.notation[0] in 'KQRBN' else 'P']

    @property
    def y(self):
        return int(self.notation[-1])-1

    @property
    def x(self):
        return San.file_to_idx[self.notation[-2]]

    @property
    def target(self):
        return board.get(self.x, self.y)

    def checkresigned(self):
        if self.notation == '1-0':
            self.special = San.blackresigned
        elif self.notation == '0-1':
            self.special = San.whiteresigned

def alternatecolour():
    while True:
        yield WHITE
        yield BLACK

# main flow
running = True
board = Board()
while running:
    colouralternator = alternatecolour()
    while board.winner is None:
        err = '\n'
        current = next(colouralternator)
        while True:
            try:
                print('\033[H\033[J') # clear screen
                print('        Welcome to Chess.py!\n Use the standard algebraic notation\n to play.     by codinggentleman.com\n')
                print(board)
                inp = input('\n {} {}: '.format(err, current))
                board.move(current, San(inp))
            except ValueError as e:
                err = '{}\n'.format(cgi(e, fg=CLI_RED, bg=''))
            else:
                break

    running = input('\n Congratulations to {}!\n New Game?[y/n]'.format(board.winner)) == 'y'
    board = Board()
