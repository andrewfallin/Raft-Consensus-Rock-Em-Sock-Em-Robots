# _________________________________
# --------- SERVER CLASS ---------
# =================================
import copy
import math
import random
import socket
import time
from threading import Thread

import jsonpickle

from ElectionMessage import ElectionMessage
from FollowerMessage import FollowerMessage
from GameState import GameState
from LeaderMessage import LeaderMessage
from Log import Log

DELIMITER = "$"


class Server:
    """Class representing a server node in the Raft consensus project"""

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
        self.clusterReady = False
        self.receiverThread = None
        self.senderThread = None
        self.clockThread = None
        self.testCommandThread = None
        self.isFailed = False

        # LEADER MANAGEMENT ATTRIBUTES
        self.isFollower = True
        self.currentLeader = -1
        self.timeout = self.getRandomTimeout(5, 15)  # TODO - Tune upper and lower bound of timeout to AWS cluster
        self.clock = self.timeout
        self.isLeader = False
        self.heartRate = 3  # TODO - Arbitrary
        self.isCandidate = False
        self.acksReceived = 0
        # TODO - Need to check if we receive something from a server while election and check its term vs ours
        self.prevLogTerm = 0
        self.currentTerm = 0
        self.hasVoted = False

        self.votesReceived = 0
        # len group - 2 (client nodes) / 2(to get the majority ... rounded up
        self.majority = math.ceil(len(group) / 2)
        # print("Majority" + str(self.majority))

        # GAME STATE & LOG ATTRIBUTES
        self.currentGameState = GameState()
        self.log = Log()

        # TODO - Helper methods to modify group size based on testing needs
        # self.createTwoClientThreeServerGroup()
        # self.createOnlyThreeServerGroup()

    # __________________________________________
    # --------- MAIN EXECUTION LOOPS -----------
    # ==========================================
    def mainOutgoingLoop(self) -> None:
        """The main loop that drives the server's behavior in Raft (with the listening loop triggering actions here)"""
        print("Sender thread started...")
        while True:
            if self.isFailed is False:
                # Leader Logic
                if self.isLeader is True:
                    self.pulseHeartbeat()
                # Follower Logic
                elif self.isFollower is True:
                    # Follower Times Out
                    if self.clock <= 0:
                        print("TIMEOUT! Initiating election...\n")
                        self.initiateElection()
            else:
                print("FAILED")
                time.sleep(1)

    def mainIncomingLoop(self) -> None:
        """Runs an infinite loop listening for messages from other processes in the group,
        accessing/modifying local data as needed"""
        print("Receiver thread started...\n")
        while True:
            # On receipt of a message, decode data
            data, address = self.socket.recvfrom(16384)
            address = [0, address[0], address[1]]
            data = data.decode("utf-8")
            # RAW MESSAGE PRINT FOR TESTING
            # print("\n" + data + "\n")
            if self.isFailed is False:
                # Logic for if message is to start complete cluster
                if data[0] == "S":
                    self.clusterReady = True
                # Logic for if message was a heart beat
                elif data[0] == "H":
                    print("Heartbeat received...\n")
                    self.hearHeartbeat()
                # Logic for if message was an election request
                elif data[0] == "E":
                    splitData = data.split(DELIMITER)
                    electionMessage = jsonpickle.decode(splitData[1])
                    print("Election initiated by Server " + str(electionMessage.eid) + "...\n")
                    self.castVote(electionMessage, address)
                # Logic for if message was a negative vote
                elif data[0] == "N":
                    print("No vote received by Server " + data[-1] + "...\n")
                # Logic for if message was a positive vote
                elif data[0] == "Y":
                    print("Yes vote received by Server " + data[-1] + "...\n")
                    self.countYesVote()
                # Logic for if message was a won election announcement
                elif data[0] == "W":
                    print("Election won by Server " + data[-1] + "...\n")
                    self.hearWonElection(data[-1])
                # Logic for if we receive a commit message from leader
                elif data[0] == "C":
                    self.log.commitEntryToLog()
                    # every time we commit we write to our backup
                    self.writeLogtoFile()
                # logic for updating incorrect logs
                elif data[0] == "U":
                    splitData = data.split(DELIMITER)
                    leaderMsg = jsonpickle.decode(splitData[1])
                    # check to see if we still have a log inconsistnecy
                    # if self.checkForLogInconsistency(leaderMsg):
                    #    acked = False
                    #   print(self.log.logList)
                    # else:
                    # no log inconsistency so we append the missing log entries to our log
                    #  self.log.appendEntriesToLog(leaderMsg.entries)
                    #   print(self.log.logList)
                    #   acked = True
                    self.log.logList = leaderMsg.entries
                    self.log.lastCommittedEntry = leaderMsg.lastCommittedEntry
                    self.log.lastAppendedEntry = leaderMsg.lastAppendedEntry
                    acked = True
                    # ack the leader with either we were successful or not
                    newPickle = self.getFollowerResponseMsg(acked)
                    message = "A" + DELIMITER + newPickle
                    self.sendMessage(address, message)
                # Logic for acking message from leader
                elif data[0] == "R":
                    splitData = data.split(DELIMITER)
                    leaderMsg = jsonpickle.decode(splitData[1])
                    # need to send message back to leader
                    # need to append to log
                    acked = True
                    if not self.isLeader:
                        if self.log.nextIndex <= leaderMsg.lastAppendedEntry:
                            acked = False
                        elif self.checkForLogInconsistency:
                            acked = False
                        else:
                            # if there are no issues we add it to our log and ack the leader
                            self.currentGameState = leaderMsg.entries
                            self.log.appendEntryToLog(copy.deepcopy(
                                self.currentGameState), self.currentTerm)
                        newPickle = self.getFollowerResponseMsg(acked)
                        message = "A" + DELIMITER + newPickle
                        self.sendMessage(address, message)
                # Logic for receiving an Ack
                elif data[0] == "A":
                    splitData = data.split(DELIMITER)
                    # using pickle so the message is easier to parse
                    followerMsg = jsonpickle.decode(splitData[1])
                    if followerMsg.response:
                        self.acksReceived += 1
                    else:
                        # sends a message back to the behind process
                        # correctionMessage = self.getLeaderMsg(self.log.getSubLog(followerMsg.nextIndex))
                        correctionMessage = self.getLeaderMsg(self.log.logList)
                        message = "U" + DELIMITER + correctionMessage
                        self.sendMessage(address, message)
                    # if we receive enoough acks we tell the servers to commit the message
                    if self.acksReceived >= self.majority:
                        # set our acks to 0 to prevent sending messages multiple times
                        self.acksReceived = 0
                        # tell the servers to commit item
                        print("Enough Acks received sending commit message... ")
                        for i in range(self.log.lastCommittedEntry, self.log.lastAppendedEntry):
                            self.log.commitEntryToLog()
                        self.messageServers("C")
                        # inform the client of action outcome
                        self.announceOutcome()
                        gamestateGraphic = self.currentGameState.getGameStateGraphic()
                        self.messageClients(self.currentGameState.outcome + DELIMITER + gamestateGraphic)
                # Logic for if message was an action sent to the server cluster by a client
                elif data[0] == "0" or data[0] == "1":
                    # TODO - Improve so that all handle message, not just leader (i.e. this is very fragile)
                    if self.isLeader is True:
                        self.announceAction(data)
                        self.currentGameState.updateGameState(data)
                        self.log.appendEntryToLog(copy.deepcopy(
                            self.currentGameState),
                            self.currentTerm)  # NOTE: Current Gamestate is updated in place, hence the copy
                        messageToServers = self.getLeaderMsg(self.currentGameState)
                        message = "R" + DELIMITER + messageToServers
                        self.acksReceived = 0
                        self.messageServers(message)

    def mainClockLoop(self) -> None:
        """Runs an infinite loop that executes countdown timers independent of the other loops"""
        # Bring up all clusters at once with single command at Server_2
        if self.id == 2:
            time.sleep(0.25)  # Minor delay lets other threads come online before prompt
            self.startCompleteCluster()
        while self.clusterReady is False:
            time.sleep(1)  # Sleep the clock thread until the START message is received by Server_2
        print("Clock thread started...\n")
        # Runs clock
        while True:
            if self.isFailed is False:
                # Display clock and decrement
                minutes, seconds = divmod(self.clock, 60)
                timeFormat = "{:02d}:{:02d}".format(minutes, seconds)
                print(timeFormat, end="\r")
                time.sleep(1)
                self.clock -= 1

    def testCommandLoop(self) -> None:
        """Runs an infinite loop that awaits user commands to force failures, recovers, and timeouts"""
        while self.clusterReady is False:
            time.sleep(1)
        while True:
            testCommand = input()
            if testCommand == "t":
                if self.isFollower is True:
                    self.clock = 0
            elif testCommand == "f":
                self.isFailed = True
            elif testCommand == "s":
                self.isFailed = False
            elif testCommand == "r":
                self.loadAndRecoverLog()
                self.isFailed = False
            elif testCommand == "l":
                self.loadAndRecoverLog()
            elif testCommand == "p":
                self.log.printLogEntries()
                print("\nLog as Object:")
                print(self.log.logList)

    # _______________________________________
    # --------- HEARTBEAT METHODS -----------
    # =======================================
    def pulseHeartbeat(self) -> None:
        """Pulses the leader's heart beat"""
        if self.clock <= 0:
            print("Sending heartbeat...\n")
            for process in self.group:
                if process[0][0] == "S":  # Multicast to servers only
                    self.sendMessage(process, "H")
            self.clock = self.heartRate

    def hearHeartbeat(self) -> None:
        """Listens for the heartbeat from a leader and responds with current log state"""
        self.clock = self.timeout

    # _____________________________________________
    # --------- LEADER ELECTION METHODS -----------
    # =============================================
    def initiateElection(self) -> None:
        """Initiates an election when a follower node has timed out"""
        # Flips identity from follower to candidate and casts vote for self
        self.isFollower = False
        self.isCandidate = True
        # since it is initiating an election it needs to increment it current term
        self.currentTerm = self.currentTerm + 1
        # need to say that it has already voted this term set 'hasVoted' to true
        self.hasVoted = True
        self.votesReceived = 1
        electionPickle = self.getElectionMessage()
        message = "E" + DELIMITER + electionPickle
        # Broadcast request for votes
        for process in self.group:
            if process[0][0] == "S":
                self.sendMessage(process, message)

    def castVote(self, electionMessage: ElectionMessage, senderAddress) -> None:
        """Casts a positive or negative vote for a candidate node"""
        candidate = electionMessage.eid
        if electionMessage.currentTerm < self.currentTerm:
            # if their current term is less than ours then they are behind
            vote = "N_"
        elif electionMessage.lastLogIndex < self.log.lastCommittedEntry:
            # if their last committed entry is less than ours then they are behind
            vote = "N_"
        elif self.hasVoted:
            # we have already voted
            vote = "N_"
        else:
            # none of the above restrictions apply so we vote yes
            vote = "Y_"
            self.hasVoted = True
        # candidateAddress = self.getProcessAddressing(candidate)
        self.sendMessage(senderAddress, vote + str(self.id))

    def countYesVote(self) -> None:
        """Counts a positive vote for the candidate and declares the election if a majority has been reached"""
        self.votesReceived += 1
        # If the election is won, end the election and become leader
        if self.votesReceived >= self.majority and self.isCandidate is True:
            self.isCandidate = False
            self.hasVoted = False
            self.votesReceived = 0
            self.isLeader = True
            self.currentLeader = self.id
            self.broadcastElectionWin()

    def broadcastElectionWin(self) -> None:
        """Broadcasts an election win to the group"""
        for process in self.group:
            if process[0][0] == "S":
                self.sendMessage(process, "W_" + str(self.id))

    def hearWonElection(self, newLeader: str) -> None:
        """Receives an announcement of an election win and updates leadership accordingly"""
        self.isFollower = True
        self.isCandidate = False
        self.isLeader = False
        self.hasVoted = False
        self.votesReceived = 0
        self.currentLeader = int(newLeader)
        self.currentTerm += 1

    # _______________________________________
    # --------- MESSAGING METHODS -----------
    # =======================================
    def sendMessage(self, recipientAddressing, message: str) -> None:
        """Sends a message as a string to a recipient"""
        self.socket.sendto(message.encode("utf-8"), (recipientAddressing[1], recipientAddressing[2]))
        # print("\nMessage sent to " + recipientAddressing[0] + " at " + recipientAddressing[1] + ":" + str(recipientAddressing[2]) + "...\n")

    def messageServers(self, message: str) -> None:
        """ Multicasts messages to all servers """
        for process in self.group:
            if process[0][0] == "S":  # Multicast to servers
                self.sendMessage(process, message)

    def messageClients(self, message: str) -> None:
        """Multicasts a message just to the clients"""
        for process in self.group:
            if process[0][0] == "C":  # Multicast to clients
                self.sendMessage(process, message)

    # ____________________________________
    # --------- HELPER METHODS -----------
    # ====================================
    def startThreads(self) -> None:
        """Boots-up both the sender and receiver threads"""
        self.senderThread = Thread(target=self.mainOutgoingLoop, args=())
        self.senderThread.start()
        self.receiverThread = Thread(target=self.mainIncomingLoop, args=())
        self.receiverThread.start()
        self.testCommandThread = Thread(target=self.testCommandLoop, args=())
        self.testCommandThread.start()
        self.clockThread = Thread(target=self.mainClockLoop, args=())
        self.clockThread.start()

    def announceOutcome(self) -> None:
        """Concatenates the outcome details and prints them"""
        robot = "RED "
        if self.currentGameState.outcome[-1] == "1":
            robot = "BLUE "
        outcome = "was unaffected!"
        if self.currentGameState.outcome[0] == "B":
            outcome = "blocked the punch!"
        elif self.currentGameState.outcome[0] == "K":
            outcome = "was KNOCKED OUT!\n\n\tGAME OVER!!!"
        print(robot + outcome)

    @staticmethod
    def announceAction(data: str) -> None:
        """Constructs the action from the message and concatenates for printing"""
        robot = "RED "
        if data[0] == "1":
            robot = "BLUE "
        action = "threw a PUNCH with their "
        if data[-1] == "A" or data[-1] == "S":
            action = "has a BLOCK up with their "
        hand = "LEFT!\n"
        if data[-1] == "W" or data[-1] == "S":
            hand = "RIGHT!\n"
        print(robot + action + hand)

    @staticmethod
    def getRandomTimeout(lb: int, ub: int) -> int:
        """Returns a random timeout duration for follower nodes"""
        random.seed()
        return random.randint(lb, ub)

    def getProcessAddressing(self, recipientID: str) -> tuple:
        """Returns the networking tuple with the recipient's ID"""
        for process in self.group:
            if process[0][-1] == recipientID:
                return process

    def startCompleteCluster(self) -> None:
        """Brings complete server cluster online at once"""
        isReady = input("Start server cluster? (Y/N)\n-> ")
        if isReady == "y" or isReady == "Y" or isReady == "yes" or isReady == "YES":
            self.clusterReady = True
            for process in self.group:
                if process[0][0] == "S":
                    self.sendMessage(process, "S")

    def checkForLogInconsistency(self, leaderMsg):
        """ If there is a log inconsistency return True """
        acked = False
        # if the term is incorrect we need to send correct log
        if self.currentTerm < leaderMsg.currentTerm:
            acked = True
            self.currentTerm = leaderMsg.currentTerm
            self.isLeader = False
            self.isCandidate = False
            self.isFollower = False
            self.log.nextIndex -= 1
        # if we have logs of equal length but this log has been recording incorrect entries send correct log
        elif len(self.log.logList) > self.log.nextIndex and self.log.nextIndex != -1:
            if (self.log.logList[self.log.nextIndex])[1] != leaderMsg.prevLogTerm:
                acked = True
                self.log.removeItemsFromIndextoEnd(self.log.nextIndex)
                self.log.nextIndex -= 1
        elif len(self.log.logList) > self.log.lastAppendedEntry and self.log.lastAppendedEntry != -1:
            if (self.log.logList[self.log.lastAppendedEntry])[1] != leaderMsg.prevLogTerm:
                acked = True
                self.log.removeItemsFromIndextoEnd(self.log.nextIndex)
                self.log.nextIndex -= 1
        return acked

    def parseIncomingData(self, data):
        """ Splits the data by the Delimiter and returns the list """
        splitData = data.split(DELIMITER)
        return splitData

    def getLeaderMsg(self, entries):
        """ returns the encoded jsonpickle of leader message to send to servers """
        newMessage = LeaderMessage(self.currentTerm, entries, self.log.lastCommittedEntry, self.log.lastAppendedEntry,
                                   self.prevLogTerm, self.log.prevLogIndex, self.log.nextIndex)
        return jsonpickle.encode(newMessage)

    def getFollowerResponseMsg(self, response):
        """ returns the encoded jsonpickle of follower response message to send to leader """
        newMessage = FollowerMessage(self.currentTerm, response, self.log.lastCommittedEntry, self.log.nextIndex)
        return jsonpickle.encode(newMessage)

    def getElectionMessage(self):
        """ returns the encoded jsonpickle of an election message"""
        newMessage = ElectionMessage(self.id, self.currentTerm, self.log.lastCommittedEntry,
                                     self.log.getTermAtIndex(self.log.lastCommittedEntry))
        return jsonpickle.encode(newMessage)

    def writeLogtoFile(self):
        """ pickles the entire log and writes it to file """
        f = open(self.backupPath, 'w+')
        f.write(jsonpickle.encode(self.log))
        f.close()

    def loadAndRecoverLog(self):
        """ decodes the recovered log and replaces the old log """
        f = open(self.backupPath, 'r')
        pickledLog = f.read()
        self.log = jsonpickle.decode(pickledLog)
        f.close()

    def createOnlyThreeServerGroup(self) -> None:
        """Selects only p2, p3, and p4 to be in the group for easier testing"""
        self.majority = 2
        newGroup = []
        for process in self.group:
            if self.name[-1] == "2" and (process[0][-1] == "3" or process[0][-1] == "4"):
                newGroup.append(process)
            elif self.name[-1] == "3" and (process[0][-1] == "2" or process[0][-1] == "4"):
                newGroup.append(process)
            elif self.name[-1] == "4" and (process[0][-1] == "2" or process[0][-1] == "3"):
                newGroup.append(process)
        self.group = newGroup

    def createTwoClientThreeServerGroup(self) -> None:
        """Selects only p0, p1, p2, p3, and p4 to be in the group for easier testing"""
        self.majority = 2
        newGroup = []
        for process in self.group:
            if not (process[0][-1] == "5" or process[0][-1] == "6"):
                newGroup.append(process)
        self.group = newGroup
