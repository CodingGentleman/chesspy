#!/usr/bin/env python3
import re

WHITE = 'w'
BLACK = 'b'

class Chessman:
	def __init__(self, colour):
		self.colour = colour
		self.enpassante = False

	def __str__(self):
		return self.__class__.__name__.lower() if self.colour == BLACK else self.__class__.__name__

	def isopponent(self, other):
		return isinstance(other, Chessman) and other.colour != self.colour

class K(Chessman):
	def ismoveallowed(self, fromY, fromX, san):
		return True

class Q(Chessman):
	def ismoveallowed(self, fromY, fromX, san):
		return True

class R(Chessman):
	def ismoveallowed(self, fromY, fromX, san):
		return True

class B(Chessman):
	def ismoveallowed(self, fromY, fromX, san):
		return True

class N(Chessman):
	def ismoveallowed(self, fromY, fromX, san):
		return True

class P(Chessman):
	def ismoveallowed(self, fromY, fromX, san):
		self.enpassante = False
		
		# check direction
		if self.colour == WHITE and san.getY()-fromY not in range(1,3 if fromY == 1 else 2):
			return False
		if self.colour == BLACK and fromY-san.getY() not in range(1,3 if fromY == 6 else 2):
			return False
		
		# check capture
		if abs(fromX-san.getX()) == 1 and abs(fromY-san.getY()) == 1:
			passante = board.get(san.getX(), fromY)
			if isinstance(passante, san.getClass()) and self.isopponent(passante):
				self.enpassante = True
			if self.isopponent(san.target()) or self.enpassante:
				return True
		
		# check straight move
		if abs(fromX-san.getX()) == 0 and san.target() == ' ':
			# check if free double jump
			if abs(fromY-san.getY()) == 2 and board.get(san.getX(), san.getY()-(1 if self.colour == WHITE else -1)) != ' ':
				return False
			return True

		return False

class Board:
	fileToIdx = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
	def __init__(self):
		self.winner = None
		self.board = [[' ' for x in range(8)] for y in range(8)]
		for san in list(map(lambda y: San(y), 'Ra1 Nb1 Bc1 Qd1 Ke1 Bf1 Ng1 Rh1 a2 b2 c2 d2 e2 f2 g2 h2 Ra8 Nb8 Bc8 Qd8 Ke8 Bf8 Ng8 Rh8 a7 b7 c7 d7 e7 f7 g7 h7'.split())):
			chessman = san.getClass()(BLACK if san.getY()>3 else WHITE)
			self.put(san, chessman)

	def move(self, colour, san):
		if san.special is not None:
			self.special(san.special)
		else:
			chessman = self.pop(colour, san)
			self.put(san, chessman)

	def put(self, san, chessman):
		self.board[san.getY()][san.getX()] = chessman

	def pop(self, colour, san):
		for idxR, rank in enumerate(self.board):
			for idxF, field in enumerate(rank):
				if isinstance(field, san.getClass()) and field.colour == colour and field.ismoveallowed(idxR, idxF, san):
					self.board[idxR][idxF] = ' '
					if field.enpassante:
						self.board[idxR][san.getX()] = ' '
					return field
		raise ValueError('Invalid move')

	def get(self, x, y):
		return self.board[y][x]

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

CLI_BG = '\033[43m'
CLI_BOARD = '\033[90m'
CLI_WHITE = '\033[37m'
CLI_BLACK = '\033[30m'
CLI_BOLD = '\033[1m'
CLI_RESET = '\033[0m'

def display_field(field):
	if field == ' ':
		return cgi(field)
	if field.colour == BLACK:
		return cgi(field, fg=CLI_BLACK)
	return cgi(field, fg=CLI_WHITE, fw=CLI_BOLD)

def cgi(text, fg=CLI_BOARD, fw=''):
	return '{}{}{}{}{}'.format(fg, fw, CLI_BG, text, CLI_RESET)
	
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

board = Board()
colouralternator = alternatecolour()
while board.winner is None:
	err = '\n'
	current = next(colouralternator)
	while True:
		try: 
			print('\033[H\033[J') # clear screen
			print('        Welcome to Chess.py!\n Use the standard algebraic notation\n to play.     by codinggentleman.com\n')
			print(board)
			inp = input("\n{}{}: ".format(err, current))
			board.move(current, San(inp))
		except ValueError as e:
			err = '{}\n'.format(e)
		else:
			break

print('\n{} won'.format(board.winner))
