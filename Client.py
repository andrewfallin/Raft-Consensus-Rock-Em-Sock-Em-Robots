# _________________________________
# --------- CLIENT CLASS ---------
# =================================
import socket
import time
from threading import Thread

import jsonpickle

from ClientMessage import ClientMessage

DELIMITER = "$"


class Client:
    """Class representing the client nodes (i.e. the RESE robots) in the Raft consensus project"""

    # CONSTRUCTOR
    def __init__(self, nodeID: int, name: str, address: str, port: int, group: list, backupPath: str):
        self.name = name
        self.id = nodeID
        self.backupPath = backupPath
        print("Starting " + self.name + "...")

        # NETWORKING ATTRIBUTES
        self.address = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.address, self.port))
        self.group = group

        # THREAD ATTRIBUTES (Initialized with boot-up script)
        self.receiverThread = None
        self.senderThread = None

        # ADDITIONAL VARIABLES FOR OUTCOME
        self.lastOutcome = None
        self.lastAction = None

        # TODO - Helper methods to modify group size based on testing needs
        # self.createTwoClientThreeServerGroup()

    # ___________________________________________
    # --------- REPL UI DRIVER METHOD -----------
    # ===========================================
    def beginReplUI(self) -> None:
        """Runs the read-evaluate-print-loop interface for the process,
        accessing/modifying local data and sending messages to other processes in the group as needed"""
        print("Sender thread started...")
        print(self.name + " fully online!\n")
        self.printReplMenu()
        while True:  # userInput = input("\nEnter Command:\n-> ")
            userInput = input()
            if userInput == "Q" or userInput == "q":
                message = str(self.id) + "_Q"
                self.lastAction = message
                self.multicastToServers(message)
            elif userInput == "W" or userInput == "w":
                message = str(self.id) + "_W"
                self.lastAction = message
                self.multicastToServers(message)
            elif userInput == "A" or userInput == "a":
                message = str(self.id) + "_A"
                self.lastAction = message
                self.multicastToServers(message)
            elif userInput == "S" or userInput == "s":
                message = str(self.id) + "_S"
                self.lastAction = message
                self.multicastToServers(message)
            elif userInput == "?":
                self.printReplMenu()
            else:
                print("The command '" + userInput + "' was not recognized. Press '?' for help.")

    # _____________________________________________
    # --------- MESSAGE SENDING METHODS -----------
    # =============================================
    def multicastToServers(self, message: str) -> None:
        """Multicasts the message to all nodes in the server cluster"""
        for process in self.group:
            if process[0][0] == "S":
                self.sendMessage(process, message)

    def sendMessage(self, recipientAddressing: tuple, message: str) -> None:
        """Sends a message as a string to a recipient"""
        # print(recipientAddressing[0])
        self.socket.sendto(message.encode("utf-8"), (recipientAddressing[1], recipientAddressing[2]))
        # print("Client bytes sent:" + str(numBytesSent))
        # print("\nMessage sent to " + recipientAddressing[0] + " at " + recipientAddressing[1] + ":" + str(recipientAddressing[2]) + "...")

    # _______________________________________________
    # --------- MESSAGE RECEIVING METHODS -----------
    # ===============================================
    def listen(self) -> None:
        """Runs an infinite loop listening for messages from other processes in the group,
        accessing/modifying local data as needed"""
        print("Receiver thread started...")
        while True:
            # On receipt of a message, decode data and print
            data, address = self.socket.recvfrom(16384)
            data = data.decode("utf-8")
            splitData = self.parseIncommingMessage(data)
            self.lastOutcome = splitData[0]
            print(splitData[1])
            self.processLastOutcome()

    def processLastOutcome(self) -> None:
        # add additional last outcome responses here as needed
        if self.lastOutcome.__contains__("B"):
            if not self.lastOutcome.__contains__(str(self.id)):
                print("Punch Blocked!")
                self.initiatePunchDelay(3)
        elif self.lastOutcome.__contains__("M"):
            if not self.lastOutcome.__contains__(str(self.id)):
                if self.lastAction.__contains__("A") or self.lastAction.__contains__("S"):
                    print("Block Up!")
                    self.lastAction = None
                else:
                    print("Punch Missed!")
                    self.initiatePunchDelay(1)

    # ____________________________________
    # --------- HELPER METHODS -----------
    # ====================================
    def startThreads(self) -> None:
        """Boots-up both the sender and receiver threads"""
        self.receiverThread = Thread(target=self.listen, args=())
        self.receiverThread.start()
        self.senderThread = Thread(target=self.beginReplUI, args=())
        self.senderThread.start()

    def printReplMenu(self) -> None:
        """Prints the menu options available in the REPL UI"""
        print("\n========== " + self.name + " ==========")
        print("---------- UI MENU ----------")
        print("Press 'Q' PUNCH with LEFT")
        print("Press 'W' PUNCH with RIGHT")
        print("Press 'A' BLOCK with LEFT")
        print("Press 'S' BLOCK with RIGHT")
        print("Press '?' to reprint the menu options")

    @staticmethod
    def initiatePunchDelay(punchPenalty) -> None:
        while punchPenalty > 0:
            print(str(punchPenalty) + " seconds of penalty remaining...")
            time.sleep(1)
            punchPenalty = punchPenalty - 1
        print("Penalty Ended....FIGHT")

    @staticmethod
    def parseIncommingMessage(data):
        splitData = data.split(DELIMITER)
        return splitData

    def getClientMessageToServer(self, message):
        newMessage = ClientMessage(str(self.id), message)
        return jsonpickle.encode(newMessage)

    def createTwoClientThreeServerGroup(self) -> None:
        """Selects only p0, p1, p2, p3, and p4 to be in the group for easier testing"""
        newGroup = []
        for process in self.group:
            if not (process[0][-1] == "5" or process[0][-1] == "6"):
                newGroup.append(process)
        self.group = newGroup
