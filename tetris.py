import time
import random
import signal
import sys
import os
import platform

try: 
    import msvcrt
except ImportError: 
    pass

try:
    import select
    import tty
    import termios
except ImportError: 
    pass

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

# Tetronimos

# Note: Rotation's based on SRS guidelines:
# https://tetris.fandom.com/wiki/SRS

class TetrominoI(Piece): 
     def __init__(self): 
         super(TetrominoI, self).__init__(0, '▓', [
            ["    ", "####", "    ", "    "],
            ["  # ", "  # ", "  # ", "  # "],
            ["    ", "    ", "####", "    "],
            [" #  ", " #  ", " #  ", " #  "]])

class TetrominoJ(Piece): 
     def __init__(self): 
         super(TetrominoJ, self).__init__(1, '▒', [
            ["#  ", "###", "   "],
            [" ##", " # ", " # "],
            ["   ", "###", "  #"],
            [" # ", " # ", "## "]])

class TetrominoL(Piece): 
     def __init__(self): 
         super(TetrominoL, self).__init__(2, '░', [
            ["  #", "###", "   "],
            [" # ", " # ", " ##"],
            ["   ", "###", "#  "],
            ["## ", " # ", " # "]])

class TetrominoO(Piece): 
     def __init__(self): 
         super(TetrominoO, self).__init__(3, '█', [
            [" ## " , " ## ", "    "],
            [" ## " , " ## ", "    "],
            [" ## " , " ## ", "    "],
            [" ## " , " ## ", "    "]])

class TetrominoS(Piece): 
     def __init__(self): 
         super(TetrominoS, self).__init__(4, '&', [
            [" ##", "## ", "   "],
            [" # ", " ##", "  #"],
            ["   ", " ##", "## "],
            ["#  ", "## ", " # "]])

class TetrominoT(Piece): 
     def __init__(self): 
         super(TetrominoT, self).__init__(5, '#', [
            [" # ", "###", "   "],
            [" # ", " ##", " # "],
            ["   ", "###", " # "],
            [" # ", "## ", " # "]])

class TetrominoZ(Piece): 
     def __init__(self): 
         super(TetrominoZ, self).__init__(6, '@', [
            ["## ", " ##", "   "],
            ["  #", " ##", " # "],
            ["   ", "## ", " ##"],
            [" # ", "## ", "#  "]])

# Global print symbols:

symbolWidthMod     = 2
symbolActive       = '█' * symbolWidthMod
symbolBlank        = ' ' * symbolWidthMod
symbolLeft         = '│'
symbolRight        = '│'
symbolTop          = '─' * symbolWidthMod
symbolBottom       = '─' * symbolWidthMod
symbolUpLeft       = '┌'
symbolUpRight      = '┐'
symbolBottomLeft   = '└'
symbolBottomRight  = '┘'

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
            print("CHECK CLEAR")
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
        result = symbolUpLeft + symbolTop * self.width + symbolUpRight + '\n'
        for y in range(self.height):
            result = result + symbolLeft
            for x in range(self.width):
                result = result + (symbolBlank if self.get(x,y) is None else self.get(x,y).symbol * 2)
            result = result + symbolRight + '\n'
        result = result + symbolBottomLeft + symbolTop * self.width + symbolBottomRight
        print(result)

# The Player class
# Player logic should be implemented in child classes
class Player:

    NO_ACTION   = 0
    DROP_NOW    = 1
    MOVE_LEFT   = 2
    MOVE_RIGHT  = 3
    ROTATE      = 4
    QUIT        = 5

    # Player chooses their next move
    # Can return one of the following:
    # - NO_ACTION : nothing happens
    # - DROP_NOW : immediately drops the active piece to it's final position
    # - MOVE_LEFT : moves the active piece left one block
    # - MOVE_RIGHT : moves the active piece right one block
    # - ROTATE : rotate the active piece clockwise
    # - QUIT : forfit the game
    def nextMove(self, tetris, board):
        pass

# Debuging:

debugSleep = True
debugSpeed = 20

# Tetris game state
class Tetris:

    def __init__(self, width, height, player, speed):

        self.player     = player                # Active player
        self.board      = Board(width, height)  # The active game board
        self.score      = 0                     # The current player score
        self.nextPiece  = None                  # The next piece to be played
        self.gameSpeed  = speed                 # Speed of gameplay (higher is faster)

    # Return system time in milliseconds
    def getTime(self):
        return int(round(time.time() * 1000))

    # Return a new random piece
    def genNextPiece(self):
        num = random.randint(0, 6)
        if   num == 0: return TetrominoI()
        elif num == 1: return TetrominoJ()
        elif num == 2: return TetrominoL()
        elif num == 3: return TetrominoO()
        elif num == 4: return TetrominoS()
        elif num == 5: return TetrominoT()
        elif num == 6: return TetrominoZ()

    # Run the game
    def run(self):

        self.print()
        self.nextPiece = self.genNextPiece()

        while True:

            # Force sleep for debugging
            if debugSleep:
                time.sleep(1 / debugSpeed)

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
        titleStr = " [" + str(self.board.width) + ", " + str(self.board.height) + "] Tetris:"
        scoreStr = " Score: " + str(self.score)
        result = symbolUpLeft + symbolTop * self.board.width + symbolUpRight + '\n'
        result = result + symbolLeft + titleStr + \
            (' ' * (self.board.width * symbolWidthMod - len(titleStr))) + symbolRight + '\n'
        result = result + symbolLeft + scoreStr + \
            (' ' * (self.board.width  *symbolWidthMod - len(scoreStr))) + symbolRight + '\n'
        result = result + symbolBottomLeft + symbolTop * self.board.width + symbolBottomRight
        print(result)
        self.board.print()


###########################################################################################################

# Non-blocking single character input
# Code sourced from: https://stackoverflow.com/questions/2408560/python-nonblocking-console-input
def getInput():

    # Windows platform
    if platform.system() == "Windows":
        val = ''
        while msvcrt.kbhit():
            val = val + str(msvcrt.getch())
        return val if val is not '' else None

    # Unix Platform
    else:
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)

    return None

# Basic user-input player
class UserPlayer(Player):

    KEY_UP      = "b'\\xe0'b'H'"
    KEY_DOWN    = "b'\\xe0'b'P'"
    KEY_RIGHT   = "b'\\xe0'b'M'"
    KEY_LEFT    = "b'\\xe0'b'K'"

    def nextMove(self, tetris, board):

        # Get key input
        key = getInput()
        if key is not None:

            if key == UserPlayer.KEY_LEFT:
                return Player.MOVE_LEFT
            
            if key == UserPlayer.KEY_RIGHT:
                return Player.MOVE_RIGHT

            if key == UserPlayer.KEY_DOWN:
                return Player.DROP_NOW

            if key == UserPlayer.KEY_UP:
                return Player.ROTATE

        return Player.NO_ACTION
        
# Experemental Keybord Interrupt (only works with CTRL + C)
def keyboardInterruptHandler(signal, frame):
    print("Game Ended Forcefully.")
    exit(0)

if __name__ == "__main__":

    # This was an experiment and will likely be removed
    signal.signal(signal.SIGINT, keyboardInterruptHandler)

    player = UserPlayer()
    game = Tetris(10, 20, player, 5)
    game.run()