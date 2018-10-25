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

    def __str__(self):
        return self.__class__.__name__.lower() if self.colour == BLACK else self.__class__.__name__

    def is_placeable(self, other):
        return other == FIELD or self.is_opponent(other)

    def is_opponent(self, other):
        return isinstance(other, Chessman) and other.colour != self.colour

    def is_move_allowed(self, mv):
        return self.is_placeable(mv.target.get) and self._is_move_allowed(mv)

class K(Chessman):
    def _is_move_allowed(self, mv):
        return mv.dy < 2 and mv.dx < 2

class R(Chessman):
    def _is_move_allowed(self, mv):
        if (mv.dy != 0) == (mv.dx != 0):
            return False
        for x in mv.itx:
            if board.get(x, mv.source.y) != FIELD:
                return False
        for y in mv.ity:
            if board.get(mv.source.x, y) != FIELD:
                return False
        return True

class B(Chessman):
    def _is_move_allowed(self, mv):
        if mv.dy != mv.dx:
            return False
        for x in mv.itx:
            y = next(mv.ity)
            if board.get(x, y) != FIELD:
                return False
        return True

class Q(R, B):
    def _is_move_allowed(self, mv):
        return R._is_move_allowed(self, mv) \
            or B._is_move_allowed(self, mv)

class N(Chessman):
    def _is_move_allowed(self, mv):
        return (mv.dy == 2 and mv.dx == 1) or (mv.dy == 1 and mv.dx == 2)

class P(Chessman):
    def _is_move_allowed(self, mv):
        is_on_start_rank = mv.source.y == (1 if self.colour == WHITE else 6)

        # check direction
        if self.colour == WHITE and mv.target.y - mv.source.y < 0:
            return False
        if self.colour == BLACK and mv.source.y - mv.target.y < 0:
            return False

        # check capture
        if mv.dx == 1 and mv.dy == 1:
            passante = board.get(mv.target.x, mv.source.y)
            if isinstance(passante, mv.piece_type) \
            and self.is_opponent(passante) \
            and board.history[-1].special == Move.pawn_double:
                mv.special = Move.en_passante
                return True
            return self.is_opponent(mv.target.get)

        # check straight move
        if mv.dx == 0 and mv.target.get == FIELD:
            # check if free double jump
            if mv.dy == 2:
                hurdle = board.get(mv.target.x, mv.target.y-(1 if self.colour == WHITE else -1))
                mv.special = Move.pawn_double
                return is_on_start_rank and hurdle == FIELD
            return mv.dy == 1

        return False

class Board(object):
    start_state = 'Ra1 Nb1 Bc1 Qd1 Ke1 Bf1 Ng1 Rh1 a2 b2 c2 d2 e2 f2 g2 h2 ' \
                 +'Ra8 Nb8 Bc8 Qd8 Ke8 Bf8 Ng8 Rh8 a7 b7 c7 d7 e7 f7 g7 h7'
    def __init__(self):
        self.winner = None
        self.__history = []
        self.board = [[FIELD for x in range(8)] for y in range(8)]
        moves = [Move(p) for p in Board.start_state.split()]
        for mv in moves:
            chessman = mv.piece_type(BLACK if mv.target.y > 3 else WHITE)
            self.board[mv.target.y][mv.target.x] = chessman

    def move(self, colour, mv):
        if mv.special is not None:
            self.special(mv.special)
        else:
            chessman = self.pop(colour, mv)
            self.put(mv, chessman)
        self.__history.append(mv)

    def put(self, mv, chessman):
        if isinstance(self.get(mv.target.x, mv.target.y), K):
            self.winner = chessman.colour
        self.board[mv.target.y][mv.target.x] = chessman
        self.try_promote(mv)

    def pop(self, colour, mv):
        for idxR, rank in enumerate(self.board):
            for idxF, field in enumerate(rank):
                mv.source = Position(idxF, idxR)
                if isinstance(field, mv.piece_type) and field.colour == colour and field.is_move_allowed(mv):
                    self.board[idxR][idxF] = FIELD
                    if mv.special == Move.en_passante:
                        self.board[idxR][mv.target.x] = FIELD
                    return field
        raise ValueError('Invalid move')

    def get(self, x, y):
        return self.board[y][x]

    @property
    def history(self):
        return self.__history

    def try_promote(self, mv):
        if isinstance(mv.target.get, P) and (mv.target.y == 0 or mv.target.y == 7):
            self.board[mv.target.y][mv.target.x] = Q(mv.target.get.colour)

    def win(self, colour):
        self.winner = colour

    def special(self, mv_special):
        if mv_special == Move.black_resigned:
            self.win(WHITE)
        if mv_special == Move.white_resigned:
            self.win(BLACK)

    def __str__(self):
        res = ['    a   b   c   d   e   f   g   h']
        idx = 8
        for rank in reversed(self.board):
            res.append('  '+cgi('+---+---+---+---+---+---+---+---+'))
            res.append(str(idx)+' '+cgi('| ')+cgi(' | ').join(list(map(display_field, rank)))+cgi(' |')+' '+str(idx))
            idx -= 1
        res.append('  '+cgi('+---+---+---+---+---+---+---+---+'))
        res.append('    a   b   c   d   e   f   g   h')
        return '\n'.join(res)

def display_field(field):
    if field == FIELD:
        return cgi(field)
    if field.colour == BLACK:
        return cgi(field, fg=CLI_BLACK)
    return cgi(field, fg=CLI_WHITE, fw=CLI_BOLD)

def cgi(text, fg=CLI_BOARD, bg=CLI_BG, fw=''):
    return '{}{}{}{}{}'.format(fg, fw, bg, text, CLI_RESET)

# standard algebraic notation
class Move(object):
    file_to_idx = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    san_regex = r'^([NBRQK])?([a-h])?([1-8])?(x)?([a-h][1-8])(=[NBRQK])?(\+|#)?$|^O-O(-O)?$|^1-0$|^0-1$'
    black_resigned = 'br'
    white_resigned = 'wr'
    pawn_double = 'pd'
    en_passante = 'ep'

    def __init__(self, san):
        if not re.match(Move.san_regex, san):
            raise ValueError('{} is not a valid SAN expression'.format(san))
        self.san = san
        self._target = Position(Move.file_to_idx[self.san[-2]], int(self.san[-1])-1)
        self._source = None
        self._ity = None
        self._itx = None
        self.special = self.__check_special()

    def __str__(self):
        return self.san

    @property
    def piece_type(self):
        return globals()[self.san[0] if self.san[0] in 'KQRBN' else 'P']

    @property
    def dy(self):
        return abs(self._target.y - self._source.y)

    @property
    def dx(self):
        return abs(self._target.x - self._source.x)

    @property
    def target(self):
        return self._target

    @property
    def source(self):
        return self._source

    @property
    def ity(self):
        return self._ity

    @property
    def itx(self):
        return self._itx

    @source.setter
    def source(self, value):
        self._source = value
        self._ity = nearing(value.y, self.target.y)
        self._itx = nearing(value.x, self.target.x)

    def __check_special(self):
        if self.san == '1-0':
            return Move.black_resigned
        elif self.san == '0-1':
            return Move.white_resigned
        return None

class Position(object):
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def get(self):
        return board.get(self._x, self._y)

def nearing(_from, _to):
    if _from == _to:
        return None
    step = 1 if _to > _from else -1
    it = _from
    while it != (_to-step):
        it += step
        yield it

def alternate_colour():
    while True:
        yield WHITE
        yield BLACK

# main flow
board = Board()
colour_alternator = alternate_colour()
while board.winner is None:
    err = '\n'
    current = next(colour_alternator)
    while True:
        try:
            print('\033[H\033[J\n        Welcome to Chess.py!\n Use the standard algebraic notation\n to play.     by codinggentleman.com\n')
            print(board)
            inp = Move(input('\n {} {}: '.format(err, current)))
            board.move(current, inp)
        except ValueError as e:
            err = '{}\n'.format(cgi(e, fg=CLI_RED, bg=''))
        else:
            break

print('\n Congratulations to {}!'.format(board.winner))
