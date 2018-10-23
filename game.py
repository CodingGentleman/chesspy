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
		return other.colour != self.colour

class K(Chessman):
	def ismoveallowed(self, fromX, fromY, san):
		return True

class Q(Chessman):
	def ismoveallowed(self, fromX, fromY, san):
		return True

class R(Chessman):
	def ismoveallowed(self, fromX, fromY, san):
		return True

class B(Chessman):
	def ismoveallowed(self, fromX, fromY, san):
		return True

class N(Chessman):
	def ismoveallowed(self, fromX, fromY, san):
		return True

class P(Chessman):
	def ismoveallowed(self, fromX, fromY, san):
		self.enpassante = False
		if abs(fromY-san.getY()) == 1 and board[fromX][san.getY()].isopponent(self):
			self.enpassante = True
		return True

class Board:
	fileToIdx = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
	def __init__(self):
		self.board = [[' ' for x in range(8)] for y in range(8)]
		for san in list(map(lambda y: San(y), 'Ra1 Nb1 Bc1 Qd1 Ke1 Bf1 Ng1 Rh1 a2 b2 c2 d2 e2 f2 g2 h2 Ra8 Nb8 Bc8 Qd8 Ke8 Bf8 Ng8 Rh8 a7 b7 c7 d7 e7 f7 g7 h7'.split())):
			chessman = san.getClass()(BLACK if san.getX()>3 else WHITE)
			self.put(san, chessman)

	def move(self, colour, san):
		chessman = self.pop(colour, san)
		self.put(san, chessman)
	
	def put(self, san, chessman):
		self.board[san.getX()][san.getY()] = chessman
	
	def pop(self, colour, san):
		for idxR, rank in enumerate(self.board):
			for idxF, field in enumerate(rank):
				if isinstance(field, san.getClass()) and field.colour == colour and field.ismoveallowed(idxR, idxF, san):
					self.board[idxR][idxF] = ' '
					if chessman.enpassante:
						board[idxR][san.getY()] = ' '
					return field
		raise ValueError('Invalid move')

	def __str__(self):
		res = '  a b c d e f g h'
		idx = 8
		for rank in reversed(self.board):
			res += '\n  _______________\n'
			res += str(idx)+'|'
			res += '|'.join(list(map(str, rank)))
			res += '|'+str(idx)
			idx-=1
		res += '\n  a b c d e f g h'
		return res

# standard algebraic notation
class San:
	fileToIdx = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
	
	def __init__(self, notation):
		if not re.match(r'[BRQNK][a-h][1-8]|[BRQNK][a-h]x[a-h][1-8]|[BRQNK][a-h][1-8]x[a-h][1-8]|[BRQNK][a-h][1-8][a-h][1-8]|[BRQNK][a-h][a-h][1-8]|[BRQNK]x[a-h][1-8]|[a-h]x[a-h][1-8]=(B+R+Q+N)|[a-h]x[a-h][1-8]|[a-h][1-8]x[a-h][1-8]=(B+R+Q+N)|[a-h][1-8]x[a-h][1-8]|[a-h][1-8][a-h][1-8]=(B+R+Q+N)|[a-h][1-8][a-h][1-8]|[a-h][1-8]=(B+R+Q+N)|[a-h][1-8]|[BRQNK][1-8]x[a-h][1-8]|[BRQNK][1-8][a-h][1-8]', notation):
			raise ValueError('{} not a valid san expression'.format(notation))
		self.notation = notation
	
	def getClass(self):
		return globals()[self.notation[0] if self.notation[0] in 'KQRBN' else 'P']
	
	def getX(self):
		return int(self.notation[-1])-1
	
	def getY(self):
		return San.fileToIdx[self.notation[-2]]

def alternatecolour():
	while True:
		yield WHITE
		yield BLACK

board = Board()
colour = alternatecolour()
while True:
	print(board)
	current = next(colour)
	
	while True:
		try: 
			inp = input("\n{}: ".format(current))
			if inp == 'exit':
				exit()
			board.move(current, San(inp))
		except ValueError as err:
			print(err)
		else:
			break
