
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