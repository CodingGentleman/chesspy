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

UNICODE_PIECES = {
  'r': u'♜', 'n': u'♞', 'b': u'♝', 'q': u'♛',
  'k': u'♚', 'p': u'♟', 'R': u'♖', 'N': u'♘',
  'B': u'♗', 'Q': u'♕', 'K': u'♔', 'P': u'♙',
  None: ' '
}

class Chessman(object):
    def __init__(self, colour):
        self.colour = colour
        self._move_count = 0

    def __str__(self):
        repr = self.__class__.__name__.lower() if self.colour == BLACK else self.__class__.__name__
        return UNICODE_PIECES[repr] if use_unicode else repr

    def is_placeable(self, other):
        return other == FIELD or self.is_opponent(other)

    def is_opponent(self, other):
        return isinstance(other, Chessman) and other.colour != self.colour

    def is_move_allowed(self, mv):
        return self.is_placeable(mv.target.get) and self._is_move_allowed(mv)

    def inc_move_count(self):
        self._move_count += 1

    @property
    def move_count(self):
        return self._move_count

class K(Chessman):
    def is_move_allowed(self, mv):
        if mv.special is None:
            return super(K, self).is_move_allowed(mv)
        if mv.special.startswith(Move.castling_prefix):
            return self.__is_cycling_allowed(mv)
        return False

    def _is_move_allowed(self, mv):
        return mv.dy < 2 and mv.dx < 2

    def __is_cycling_allowed(self, mv):
        if self.move_count != 0 or mv.target.get.move_count != 0:
            return False
        for x in mv.itx:
            if board.get(x, mv.source.y) != FIELD:
                return False
        return True

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
                return self.move_count == 0 and hurdle == FIELD
            return mv.dy == 1

        return False

class Board(object):
    start_state = 'Ra1 Nb1 Bc1 Qd1 Ke1 Bf1 Ng1 Rh1 a2 b2 c2 d2 e2 f2 g2 h2 ' \
                 +'Ra8 Nb8 Bc8 Qd8 Ke8 Bf8 Ng8 Rh8 a7 b7 c7 d7 e7 f7 g7 h7'
    def __init__(self):
        self.winner = None
        self.__history = []
        self.board = [[FIELD for x in range(8)] for y in range(8)]
        moves = [Move(p, WHITE) for p in Board.start_state.split()]
        for mv in moves:
            chessman = mv.piece_type(BLACK if mv.target.y > 3 else WHITE)
            self.board[mv.target.y][mv.target.x] = chessman

    def move(self, colour, mv):
        if mv.special is not None:
            self.special(colour, mv)
        else:
            chessman = self.pop(colour, mv)
            self.put(mv, chessman)
        self.__history.append(mv)

    def put(self, mv, chessman):
        if isinstance(self.get(mv.target.x, mv.target.y), K):
            self.winner = chessman.colour
        self.__set(mv.target.x, mv.target.y, chessman)
        self.try_promote(mv)

    def __set(self, x, y, chessman):
        self.board[y][x] = chessman
        chessman.inc_move_count()

    def pop(self, colour, mv):
        for idxR, rank in enumerate(self.board):
            for idxF, field in enumerate(rank):
                mv.source = Position(idxF, idxR)
                if isinstance(field, mv.piece_type) and field.colour == colour and field.is_move_allowed(mv):
                    self.__clear(idxF, idxF)
                    if mv.special == Move.en_passante:
                        self.__clear(mv.target.x, idxR)
                    return field
        raise ValueError('Invalid move')

    def __pop(self, x, y):
        field = self.get(x, y)
        self.__clear(x, y)
        return field

    def __clear(self, x, y):
        self.board[y][x] = FIELD

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

    def special(self, colour, mv):
        if mv.special == Move.black_resigned:
            self.win(WHITE)
        if mv.special == Move.white_resigned:
            self.win(BLACK)
        if mv.special.startswith(Move.castling_prefix):
            # set king as source
            rank = 0 if colour == BLACK else 7
            k = self.pop(colour, mv)
            if mv.special == Move.castling_kingside:
                r = self.get(rank, 7)
                self.__set(mv.source.x + 2, mv.source.y, k)
                self.__set(mv.target.x - 2, mv.target.y, r)
                self.board[rank][mv.target.x] = FIELD
            else:
                r = self.get(rank, 0)
                self.__set(mv.source.x - 2, mv.target.y, k)
                self.__set(mv.target.x + 3, mv.target.y, r)
                self.board[move.target.y][mv.target.x] = FIELD

    def __display_board(self):
        res = ['    a   b   c   d   e   f   g   h']
        idx = 8
        for rank in reversed(self.board):
            res.append('  '+cgi('+---+---+---+---+---+---+---+---+'))
            res.append(str(idx)+' '+cgi('| ')+cgi(' | ').join(list(map(display_field, rank)))+cgi(' |')+' '+str(idx))
            idx -= 1
        res.append('  '+cgi('+---+---+---+---+---+---+---+---+'))
        res.append('    a   b   c   d   e   f   g   h')
        return res

    def __display_history(self):
        res = []
        for idx, entry in enumerate(self.history):
            if idx % 2 != 0:
                res[-1] += (' ' + str(entry))
            else:
                res.append(str(entry))
        return res

    def __str__(self):
        b_lines = self.__display_board()
        h_lines = self.__display_history()
        res = ['\033[H\033[J']
        res.append('        Welcome to Chess.py!')
        res.append(' Use the standard algebraic notation')
        res.append(' to play.     by codinggentleman.com    {}\n'.format('History:' if len(self.history) > 0 else ''))
        for idx, line in enumerate(b_lines):
            pad_len = len(line) + (40 - len(re.sub('\033[[0-9]*m', '', line)))
            line = line.ljust(pad_len)
            line += ''.join(list(map(lambda l: str(l).ljust(9), h_lines))[idx::19])
            res.append(line)
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
    castling_prefix = 'c'
    castling_kingside = 'ck'
    castling_queenside = 'cq'
    special_move_dict = {'1-0': black_resigned, '0-1': white_resigned, 'O-O': castling_kingside, 'O-O-O': castling_queenside}

    def __init__(self, san, colour):
        if not re.match(Move.san_regex, san):
            raise ValueError('{} is not a valid SAN expression'.format(san))
        self.san = san
        self.special = self.__get_special()
        self._target = self.__create_target(colour)
        self._source = None
        self._ity = None
        self._itx = None

    def __str__(self):
        return self.san

    def __create_target(self, colour):
        if self.special is not None and self.special.startswith(Move.castling_prefix):
            return Position(0 if self.special == Move.castling_queenside else 7, 0 if colour == WHITE else 7)
        return Position(Move.file_to_idx[self.san[-2]], int(self.san[-1])-1)

    @property
    def piece_type(self):
        clazz = 'P'
        if self.san[0] in 'KQRBN':
            clazz = self.san[0]
        elif self.special is not None and self.special.startswith(self.castling_prefix):
            clazz = 'K'   
        return globals()[clazz]

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
        self.__reset_iterator()

    @target.setter
    def target(self, value):
        self._target = value
        self.__reset_iterator()

    def __reset_iterator(self):
        self._ity = nearing(self.source.y, self.target.y)
        self._itx = nearing(self.source.x, self.target.x)

    def __get_special(self):
        return Move.special_move_dict.get(self.san)

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
use_unicode = False
Board.start_state = 'Ra1 Ke1 Rh1 Ra8 Ke8 Rh8'
board = Board()
colour_alternator = alternate_colour()
while board.winner is None:
    err = '\n'
    current = next(colour_alternator)
    while True:
        try:
            print(board)
            inp = Move(input('\n {} {}: '.format(err, current)), current)
            board.move(current, inp)
        except ValueError as e:
            err = '{}\n'.format(cgi(e, fg=CLI_RED, bg=''))
        else:
            break
print(board)
print('\n Congratulations to {}!'.format(board.winner))
