import time
import random

from util import setCursor, clear
from player import Player
from players.userPlayer import UserPlayer



# Global piece groups
TETRIS_PIECES       = "pieces/tetronimos.csv"

# Global print symbols:
SYMBOL_WIDTH_MOD    = 2
SYMBOL_ACTIVE       = '█' * SYMBOL_WIDTH_MOD
SYMBOL_BLANK        = ' ' * SYMBOL_WIDTH_MOD
SYMBOL_LEFT         = '│'
SYMBOL_RIGHT        = '│'
SYMBOL_TOP          = '─' * SYMBOL_WIDTH_MOD
SYMBOL_BOTTOM       = '─' * SYMBOL_WIDTH_MOD
SYMBOL_UP_LEFT      = '┌'
SYMBOL_UP_RIGHT     = '┐'
SYMBOL_BOTTOM_LEFT  = '└'
SYMBOL_BOTTOM_RIGHT = '┘'



# Load pieces from CSV path
def loadPieces(pieces):

    csv = open(pieces, encoding='utf-8')
    values = csv.read().replace('\n', '').split(',')
    pieces = list()

    while len(values) > 1:
        values.pop(0) # Pop unused name
        typeId  = int(values.pop(0))
        height  = int(values.pop(0))
        width   = int(values.pop(0))
        symbol  = values.pop(0)

        shapes  = list()

        for _ in range(height):
            shape = list()
            for _ in range(width):
                shape.append(values.pop(0))
            shapes.append(shape)

        piece = Piece(typeId, symbol, shapes)
        pieces.append(piece)

    csv.close()

    return pieces



# Tetris game piece
class Piece:

    def __init__(self, typeId, symbol, shapes):

        self.typeId     = typeId                # The numeric id of the piece type
        self.symbol     = symbol                # The printed symbol for this piece
        self.x          = 0                     # The x coord of the upper-left block
        self.y          = 0                     # The y coord of the upper-left block
        self.shapes     = shapes                # The list of possilbe shape layout rotations
        self.shape      = shapes[0]             # The current shape rotation layout
        self.width      = len(self.shape[0])    # The width of the piece    (rotation applied)
        self.height     = len(self.shape)       # The height of the piece   (rotation applied)
        self.rotation   = 0                     # The shape's rotation
                                                # - 0 : 0, 1 : 90, 2 : 180, 3 = 270

    # Set the internal position
    def set(self, x, y):
        self.x = x
        self.y = y

    # Roatate 90 degrees clockwise
    def rotateForward(self):
        self.rotation = (self.rotation + 1) % 4
        self.shape = self.shapes[self.rotation % len(self.shapes)]
        temp = self.width
        self.width = self.height
        self.height = temp

    # Roatate 90 degrees counter-clockwise
    def rotateBackward(self):
        self.rotation = (self.rotation - 1) % 4
        self.shape = self.shapes[self.rotation % len(self.shapes)]
        temp = self.width
        self.width = self.height
        self.height = temp



# Tetris game board
class Board:

    def __init__(self, width, height):

        self.width      = width                                     # The grid height
        self.height     = height                                    # The grid width
        self.grid       = [[None] * height for i in range(width)]   # The grid of pieces
        self.piece      = None                                      # The actively falling piece, if any
        self.heights    = [0] * height                              # The current maximum heights of the upper-most block for each column
        self.maxHeight  = 0                                         # The current maximum height of the upper-most block of any column
        self.minHeight  = 0                                         # The current minimum height of the upper-most block of any column

        # Note: I don't like this here
        self.lastRoundTetris = False                                # Flag if player got a tetris last round

    # Get a value of an element in the board grid
    def get(self, x, y):
        return self.grid[x][y]

    # Set a value of an element in the board grid
    def set(self, x, y, val):
        self.grid[x][y] = val

    # Check if a piece can be placed at x, y
    # Returns False if the column is out of bounds, or the piece conflicts, else True
    def canPlace(self, piece, x, y):

        # Check piece in bounds
        if self.piece is None: return False

        # Check if new piece conflicts
        for py, line in enumerate(piece.shape):
            for px, val in enumerate(line):

                # Valid block
                if val == '#':
                    
                    # Check outside grid
                    if (x + px >= self.width or x + px < 0 or y + py >= self.height):
                        return False

                    # Check collision
                    if self.get(x + px, y + py) != None: 
                        return False

        return True

    # Place a piece onto the board at x, y
    def placePiece(self, piece, x, y):
        for py, line in enumerate(piece.shape):
            for px, val in enumerate(line):
                if val == '#': self.set(x + px, y + py, piece)

    # Remove a piece from the board at x, y
    def clearPiece(self, piece, x, y):
        for py, line in enumerate(piece.shape):
            for px, val in enumerate(line):
                if val == '#': self.set(x + px, y + py, None)

    # Move the current piece down by one
    # Returns False if the current piece cannot be dropped
    def drop(self):

        # Remove initial piece to avoid self-collision
        self.clearPiece(self.piece, self.piece.x, self.piece.y)
        
        # Check if piece can be moved
        if self.canPlace(self.piece, self.piece.x, self.piece.y + 1):

            # Apply gravity to active piece
            self.placePiece(self.piece, self.piece.x, self.piece.y + 1)
            self.piece.set(self.piece.x, self.piece.y + 1)
            return True
        
        # Piece cannot be moved
        self.placePiece(self.piece, self.piece.x, self.piece.y)
        return False

    # Drops a new piece in the top-center of the board
    # Returns False if an active piece is in play
    def dropNew(self, piece):

        # Check if no active piece is in play
        if self.piece is not None: return False

        # Calculate center and drop
        posX = int((self.width / 2) + 0.5) - int((piece.width / 2) + 0.5)
        piece.set(posX, 0)
        self.placePiece(piece, posX, 0)
        self.piece = piece

        return True

    # Forcefully drops the current piece to the bottom
    def fullDrop(self):
        
        # Drop until drop() returns False
        while self.drop(): pass

    # Drop all blocks above the given row
    def dropAbove(self, row):
        for col in range(self.width):
            for i in range (row, 1, -1):
                self.set(col, i, self.get(col, i - 1))
            self.set(col, 0, None)

    # Check if the given row is full
    def isRowFull(self, row):
        for col in range(self.width):
            if not self.get(col, row) != None: return False
        return True

    # Move the active piece one block to the left
    # If the piece cannot be moved, nothing happens
    def moveLeft(self):

        self.clearPiece(self.piece, self.piece.x, self.piece.y)
        self.piece.set(self.piece.x - 1, self.piece.y)

        # Check moved collision
        if not self.canPlace(self.piece, self.piece.x, self.piece.y):
            self.piece.set(self.piece.x + 1, self.piece.y)
        
        self.placePiece(self.piece, self.piece.x, self.piece.y)

    # Move the active piece one block to the right
    # If the piece cannot be moved, nothing happens
    def moveRight(self):
        
        self.clearPiece(self.piece, self.piece.x, self.piece.y)
        self.piece.set(self.piece.x + 1, self.piece.y)

        # Check moved collision
        if not self.canPlace(self.piece, self.piece.x, self.piece.y):
            self.piece.set(self.piece.x - 1, self.piece.y)
        
        self.placePiece(self.piece, self.piece.x, self.piece.y)

    # Rotate the active piece once clockwise
    # If the piece cannot be rotated, nothing happens
    def rotate(self):

        self.clearPiece(self.piece, self.piece.x, self.piece.y)
        self.piece.rotateForward()

        # Check rotated collision
        if not self.canPlace(self.piece, self.piece.x, self.piece.y):
            self.piece.rotateBackward()
        
        self.placePiece(self.piece, self.piece.x, self.piece.y)
    
    # Updates the currently falling piece, checks for row clears, checks win/lose conditions, and updates the score
    # Returns the score gained from one tick, or None if the board has reached a losing condition.
    def update(self):
    
        score = 0

        # Check if an active piece exists
        if self.piece is None: return 0

        # Drop active piece
        if not self.drop(): 

            # Game is lost
            if self.piece.y == 0: 
                self.piece = None
                return None
            
            self.piece = None
            
        # Check for row clears
        rowsCleared = 0
        if self.piece is None:
            for i in range(self.height):
                if self.isRowFull(i):
                    self.dropAbove(i)
                    rowsCleared = rowsCleared + 1

        if rowsCleared == 4:
            if self.lastRoundTetris:
                score = 1200
            else:
                score = 800

            self.lastRoundTetris = True

        else:
            score = rowsCleared * 100

        return score

    # Print the board
    def print(self):
        result = SYMBOL_UP_LEFT + SYMBOL_TOP * self.width + SYMBOL_UP_RIGHT + '\n'
        for y in range(self.height):
            result = result + SYMBOL_LEFT
            for x in range(self.width):
                result = result + (SYMBOL_BLANK if self.get(x,y) is None else self.get(x,y).symbol * 2)
            result = result + SYMBOL_RIGHT + '\n'
        result = result + SYMBOL_BOTTOM_LEFT + SYMBOL_TOP * self.width + SYMBOL_BOTTOM_RIGHT
        print(result)



# Tetris game state
class Tetris:

    def __init__(self, width, height, player, pieces, speed):

        self.player     = player                # Active player
        self.pieces     = loadPieces(pieces)    # Load the pieces from CSV
        self.board      = Board(width, height)  # The active game board
        self.score      = 0                     # The current player score
        self.nextPiece  = None                  # The next piece to be played
        self.gameSpeed  = speed                 # Speed of gameplay (higher is faster)

    # Return system time in milliseconds
    def getTime(self):
        return int(round(time.time() * 1000))

    # Return a new random piece
    def genNextPiece(self):
        return random.choice(self.pieces)

    # Run the game
    def run(self):

        # Reset cursor position
        setCursor(0, 0)
        # Print score
        self.print()
        # Get next piece
        self.nextPiece = self.genNextPiece()

        while True:

            # Get next drop time
            nextTime = self.getTime() + ((1 / self.gameSpeed) * 1000)

            # Update player in-between drop times
            while nextTime > self.getTime():

                # Break no active piece is in play
                if self.board.piece is None: break

                # Get the player's next move
                move = self.player.nextMove(self, self.board)

                if move == Player.MOVE_LEFT:
                    self.board.moveLeft()

                elif move == Player.MOVE_RIGHT:
                    self.board.moveRight()
                
                elif move == Player.ROTATE:
                    self.board.rotate()

                elif move == Player.DROP_NOW:
                    self.board.fullDrop()
                    break

            # Attempt to drop new piece
            if self.board.dropNew(self.nextPiece):
                self.nextPiece = self.genNextPiece()

            # Update board and increment score
            score = self.board.update()
            if score is not None:
                self.score = self.score + score
                self.print()
            else: break

        # Drop final piece (for visual only)
        self.board.dropNew(self.nextPiece)
        self.print()

        print("Game Over")

    # Print the board and stats
    def print(self):
        setCursor(0, 0)
        titleStr = " [" + str(self.board.width) + ", " + str(self.board.height) + "] Tetris:"
        scoreStr = " Score: " + str(self.score)
        result = SYMBOL_UP_LEFT + SYMBOL_TOP * self.board.width + SYMBOL_UP_RIGHT + '\n'
        result = result + SYMBOL_LEFT + titleStr + \
            (' ' * (self.board.width * SYMBOL_WIDTH_MOD - len(titleStr))) + SYMBOL_RIGHT + '\n'
        result = result + SYMBOL_LEFT + scoreStr + \
            (' ' * (self.board.width  *SYMBOL_WIDTH_MOD - len(scoreStr))) + SYMBOL_RIGHT + '\n'
        result = result + SYMBOL_BOTTOM_LEFT + SYMBOL_TOP * self.board.width + SYMBOL_BOTTOM_RIGHT
        print(result)
        self.board.print()



###########################################################################################################


def choosePlayer():
    
    clear()
    setCursor(0, 0)
    
    print("\n Players: \n")
    print("\t1. User Player ")

    playerId = input("\n Choose a player: ")
    
    if(playerId == '1'):
        return UserPlayer()
    
    else:
        return choosePlayer()


if __name__ == "__main__":
    player = choosePlayer()
    game = Tetris(10, 20, player, TETRIS_PIECES, 5)
    game.run()