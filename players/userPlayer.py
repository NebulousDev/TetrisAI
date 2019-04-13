from util import getInput
from player import Player

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