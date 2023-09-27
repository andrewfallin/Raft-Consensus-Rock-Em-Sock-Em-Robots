# ___________________________________
# --------- GAMESTATE CLASS ---------
# ===================================
import random


class GameState:
    """Class representing a snapshot in time (i.e. game state) of a RESE robots match"""

    # CONSTRUCTOR
    def __init__(self):
        # ENCODING: A RESE robot's arm can be either inactive/punching (0) or blocking (1)
        self.redLeft = 0
        self.redRight = 0
        self.blueLeft = 0
        self.blueRight = 0
        # ENCODING: A string '0_Q' representing "RED LEFT PUNCH"
        self.action = ""
        # ENCODING: A string 'B_1' representing "BLOCK BY BLUE", where the possible outcomes are Missed/No Effect (M), Blocked (B), or KO'd (K)
        self.outcome = ""
        # ENCODING: A game can result in either Red's the winner (0), or Blue's the winner (1), or in-progress (2)
        self.winner = 2

    # _______________________________________
    # --------- GAMESTATE METHODS -----------
    # =======================================
    def updateGameState(self, action: str) -> None:
        """Updates the current game state based on the input action (8 possible) and returns the outcome"""
        if self.winner != 2:
            print("Match is already over!")
            return
        self.action = action
        # Update states if action was a BLOCK
        if action == "0_A":
            self.redLeft = 1
            self.outcome = "M_1"
        elif action == "0_S":
            self.redRight = 1
            self.outcome = "M_1"
        elif action == "1_A":
            self.blueLeft = 1
            self.outcome = "M_0"
        elif action == "1_S":
            self.blueRight = 1
            self.outcome = "M_0"
        # Update states if action was a PUNCH
        elif action == "0_Q":
            self.redLeft = 0  # Reset hand (in case it was blocking)
            if self.blueRight == 1:
                self.outcome = "B_1"  # If opponent was blocking, mark it a block
            else:
                if self.isHit() is True:  # Roll RNG at 10% chance
                    self.outcome = "K_1"
                    self.winner = 0  # Call it a knockout and set winner
                else:
                    self.outcome = "M_1"  # Otherwise punch missed
        elif action == "0_W":
            self.redRight = 0
            if self.blueLeft == 1:
                self.outcome = "B_1"
            else:
                if self.isHit() is True:
                    self.outcome = "K_1"
                    self.winner = 0
                else:
                    self.outcome = "M_1"
        elif action == "1_Q":
            self.blueLeft = 0
            if self.redRight == 1:
                self.outcome = "B_0"
            else:
                if self.isHit() is True:
                    self.outcome = "K_0"
                    self.winner = 1
                else:
                    self.outcome = "M_0"
        elif action == "1_W":
            self.blueRight = 0
            if self.redLeft == 1:
                self.outcome = "B_0"
            else:
                if self.isHit() is True:
                    self.outcome = "K_0"
                    self.winner = 1
                else:
                    self.outcome = "M_0"

    @staticmethod
    def isHit() -> bool:
        """Evaluates if a punch lands using the 10% RNG"""
        random.seed()
        rngRoll = random.random()
        if rngRoll < 0.10:
            return True
        else:
            return False

    def printGameState(self) -> None:
        """Prints the game state to the console"""
        print("***** GAME STATE *****")
        print("RED ROCKER: LH=" + str(self.redLeft) + "\tRH=" + str(self.redRight))
        print("BLUE BOMBER: LH=" + str(self.blueLeft) + "\tRH=" + str(self.blueRight))
        print("ACTION: " + str(self.action))
        print("OUTCOME: " + str(self.outcome))
        print("STATE: " + str(self.winner))

    def drawGameState(self) -> None:
        """Prints the current game state to the console using robot ASCII art of course"""
        print(self.getGameStateGraphic())

    def getGameStateGraphic(self) -> str:
        """Returns a single string graphic encoding of current game state for sending to client"""
        graphic = ""
        if self.winner == 2:
            graphic = graphic + "===============================\n\n"
        elif self.winner == 0:
            graphic = graphic + "*****  RED WINS!!!  *****\n\n"
        elif self.winner == 1:
            graphic = graphic + "*****  BLUE WINS!!!  *****\n\n"
        # Draw if blocking action
        if self.action[-1] == "A" or self.action[-1] == "S":
            graphic = graphic + self.getRedRobotGraphic()
            graphic = graphic + "\n"
            graphic = graphic + self.getBlueRobotGraphic()
            graphic = graphic + "\n"
        if self.action[-1] == "Q" or self.action[-1] == "W":
            if self.action[0] == "0":
                graphic = graphic + self.getRedRobotPunchGraphic()
                if self.outcome[0] == "K":
                    graphic = graphic + self.getDeadBlueRobotGraphic()
                else:
                    graphic = graphic + self.getBlueRobotGraphic()
                graphic = graphic + "\n"
            elif self.action[0] == "1":
                if self.outcome[0] == "K":
                    graphic = graphic + self.getDeadRedRobotGraphic()
                else:
                    graphic = graphic + self.getRedRobotGraphic()
                graphic = graphic + self.getBlueRobotPunchGraphic()
        return graphic

    @staticmethod
    def getDeadRedRobotGraphic() -> str:
        stringGraphic = "   *?*?*\n   [xx]  \n  /|RR|\\ \n ^ d  b ^\n"
        return stringGraphic

    @staticmethod
    def getDeadBlueRobotGraphic() -> str:
        stringGraphic = "\t   *?*?*\n\t   [xx]  \n\t  /|BB|\\ \n\t ^ d  b ^\n"
        return stringGraphic

    def getRedRobotPunchGraphic(self) -> str:
        stringGraphic = ""
        if self.action[-1] == "Q" and self.redRight == 0:
            stringGraphic = "   [00]  \n  /|RR|\\ \n O |--| \\\n   d  b  @\n"
        elif self.action[-1] == "Q" and self.redRight == 1:
            stringGraphic = " B [00]  \n |/|RR|\\ \n   |--| \\\n   d  b  @\n"
        elif self.action[-1] == "W" and self.redLeft == 0:
            stringGraphic = "   [00]  \n  /|RR|\\ \n | |--| O\n @ d  b\n"
        elif self.action[-1] == "W" and self.redLeft == 1:
            stringGraphic = "   [00] B\n  /|RR|\\| \n | |--| \n @ d  b\n"
        return stringGraphic

    def getBlueRobotPunchGraphic(self) -> str:
        stringGraphic = ""
        if self.action[-1] == "Q" and self.blueRight == 0:
            stringGraphic = "\t@  [==]  \n\t \/|BB|\\ \n\t   |%%| O \n\t   d  b\n"
        elif self.action[-1] == "Q" and self.blueRight == 1:
            stringGraphic = "\t@  [==] B\n\t \/|BB|\\|\n\t   |%%|   \n\t   d  b\n"
        elif self.action[-1] == "W" and self.blueLeft == 0:
            stringGraphic = "\t   [==] @\n\t  /|BB|\\/ \n\t O |%%|   \n\t   d  b\n"
        elif self.action[-1] == "W" and self.blueLeft == 1:
            stringGraphic = "\t B [==] @\n\t |/|BB|\\/ \n\t   |%%|   \n\t   d  b\n"
        return stringGraphic

    def getRedRobotGraphic(self) -> str:
        stringGraphic = ""
        if self.redLeft == 0 and self.redRight == 0:
            stringGraphic = "   [00]  \n  /|RR|\\ \n O |--| O\n   d  b\n"
        elif self.redLeft == 1 and self.redRight == 0:
            stringGraphic = "   [00] B \n  /|RR|\\| \n O |--|  \n   d  b\n"
        elif self.redLeft == 0 and self.redRight == 1:
            stringGraphic = " B [00]   \n |/|RR|\\  \n   |--| O \n   d  b\n"
        elif self.redLeft == 1 and self.redRight == 1:
            stringGraphic = " B [00] B \n |/|RR|\\| \n   |--|   \n   d  b\n"
        return stringGraphic

    def getBlueRobotGraphic(self) -> str:
        stringGraphic = ""
        if self.blueLeft == 0 and self.blueRight == 0:
            stringGraphic = "\t   [==]  \n\t  /|BB|\\ \n\t O |%%| O \n\t   d  b\n"
        elif self.blueLeft == 1 and self.blueRight == 0:
            stringGraphic = "\t B [==]  \n\t |/|BB|\\ \n\t   |%%| O \n\t   d  b\n"
        elif self.blueLeft == 0 and self.blueRight == 1:
            stringGraphic = "\t   [==] B\n\t  /|BB|\\|\n\t O |%%|   \n\t   d  b\n"
        elif self.blueLeft == 1 and self.blueRight == 1:
            stringGraphic = "\t B [==] B\n\t |/|BB|\\| \n\t   |%%|   \n\t   d  b\n"
        return stringGraphic


"""
gs = GameState()
gs.updateGameState("1_A")
gs.drawGameState()
time.sleep(0.5)
gs.updateGameState("0_A")
gs.drawGameState()
time.sleep(0.5)
gs.updateGameState("1_S")
gs.drawGameState()
time.sleep(0.5)
gs.updateGameState("1_Q")
gs.drawGameState()
time.sleep(0.5)
gs.updateGameState("0_W")
gs.drawGameState()
time.sleep(0.5)
"""
