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

class Chessman:
	def __init__(self, colour):
		self.colour = colour
		self.en_passante = False

	def __str__(self):
		return self.__class__.__name__.lower() if self.colour == BLACK else self.__class__.__name__

	def is_placeable(self, other):
		return other == FIELD or self.is_opponent(other)
	
	def is_opponent(self, other):
		return isinstance(other, Chessman) and other.colour != self.colour
	
	def _nearing(self, _from, _to):
		if _from == _to:
			return None
		step = 1 if _to > _from else -1
		it = _from
		while it != (_to-step):
			it += step
			yield it
	
	def is_move_allowed(self, fromY, fromX, san):
		self.dy = abs(san.getY()-fromY)
		self.dx = abs(san.getX()-fromX)
		self.ity = self._nearing(fromY, san.getY())
		self.itx = self._nearing(fromX, san.getX())
		if self.is_placeable(san.target()):
			return self._is_move_allowed(fromY, fromX, san)
		return False

class K(Chessman):
	def _is_move_allowed(self, fromY, fromX, san):
		return self.dy < 2 and self.dx < 2

class R(Chessman):
	def _is_move_allowed(self, fromY, fromX, san):
		if (self.dy == 0) != (self.dx == 0):
			for x in self.itx:
				if board.get(x, fromY) != FIELD:
					return False
			for y in self.ity:
				if board.get(fromX, y) != FIELD:
					return False
			return True
		return False

class B(Chessman):
	def _is_move_allowed(self, fromY, fromX, san):
		if self.dy == self.dx:
			for x in self.itx:
				y = next(self.ity)
				if board.get(x, y) != FIELD:
					return False
			return True
		return False

class Q(R, B):
	def _is_move_allowed(self, fromY, fromX, san):
		return R._is_move_allowed(self, fromY, fromX, san) or B._is_move_allowed(self, fromY, fromX, san)

class N(Chessman):
	def _is_move_allowed(self, fromY, fromX, san):
		return (self.dy == 2 and self.dx == 1) or (self.dy == 1 and self.dx == 2)

class P(Chessman):
	def is_move_allowed(self, fromY, fromX, san):
		self.dy = abs(san.getY()-fromY)
		self.dx = abs(san.getX()-fromX)
		self.en_passante = False
		
		# check direction
		if self.colour == WHITE and san.getY()-fromY not in range(1,3 if fromY == 1 else 2):
			return False
		if self.colour == BLACK and fromY-san.getY() not in range(1,3 if fromY == 6 else 2):
			return False
		
		# check capture
		if self.dx == 1 and self.dy == 1:
			passante = board.get(san.getX(), fromY)
			if isinstance(passante, san.getClass()) and self.is_opponent(passante):
				self.en_passante = True
			if self.is_opponent(san.target()) or self.en_passante:
				return True
		
		# check straight move
		if self.dx == 0 and san.target() == FIELD:
			# check if free double jump
			if self.dy == 2 and board.get(san.getX(), san.getY()-(1 if self.colour == WHITE else -1)) != FIELD:
				return False
			return True

		return False

class Board:
	fileToIdx = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
	def __init__(self):
		self.winner = None
		self.board = [[FIELD for x in range(8)] for y in range(8)]
		for san in list(map(lambda y: San(y), 'Ra1 Nb1 Bc1 Qd1 Ke1 Bf1 Ng1 Rh1 a2 b2 c2 d2 e2 f2 g2 h2 Ra8 Nb8 Bc8 Qd8 Ke8 Bf8 Ng8 Rh8 a7 b7 c7 d7 e7 f7 g7 h7'.split())):
			chessman = san.getClass()(BLACK if san.getY()>3 else WHITE)
			self.board[san.getY()][san.getX()] = chessman

	def move(self, colour, san):
		if san.special is not None:
			self.special(san.special)
		else:
			chessman = self.pop(colour, san)
			self.put(san, chessman)

	def put(self, san, chessman):
		if isinstance(self.get(san.getX(), san.getY()), K):
			self.winner = chessman.colour
		self.board[san.getY()][san.getX()] = chessman
		self.try_promote(san)

	def pop(self, colour, san):
		for idxR, rank in enumerate(self.board):
			for idxF, field in enumerate(rank):
				if isinstance(field, san.getClass()) and field.colour == colour and field.is_move_allowed(idxR, idxF, san):
					self.board[idxR][idxF] = FIELD
					if field.en_passante:
						self.board[idxR][san.getX()] = FIELD
					return field
		raise ValueError('Invalid move')

	def get(self, x, y):
		return self.board[y][x]

	def try_promote(self, san):
		if isinstance(san.target(), P) and (san.getY() == 0 or san.getY() == 7):
			self.board[san.getY()][san.getX()] = Q(san.target().colour)
	
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
			res += cgi(' | ').join(list(map(lambda field: display_field(field), rank)))
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
class San:
	fileToIdx = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
	blackresigned = 'br'
	whiteresigned = 'wr'

	def __init__(self, notation):
		if not re.match(r'^([NBRQK])?([a-h])?([1-8])?(x)?([a-h][1-8])(=[NBRQK])?(\+|#)?$|^O-O(-O)?$|^1-0$|^0-1$', notation):
			raise ValueError('{} is not a valid SAN expression'.format(notation))
		self.notation = notation
		self.special = None
		self.checkresigned()

	def getClass(self):
		return globals()[self.notation[0] if self.notation[0] in 'KQRBN' else 'P']

	def getY(self):
		return int(self.notation[-1])-1

	def getX(self):
		return San.fileToIdx[self.notation[-2]]
	
	def target(self):
		return board.get(self.getX(), self.getY())
	
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
