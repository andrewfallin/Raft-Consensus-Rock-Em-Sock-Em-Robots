# _____________________________
# --------- LOG CLASS ---------
# =============================
from GameState import GameState


class Log:
    """Class representing a log as a series of game states in RESE robots"""

    # CONSTRUCTOR
    def __init__(self):
        self.logList = []
        self.lastAppendedEntry = -1  # Index of the most recently added entry to the log list
        self.lastCommittedEntry = -1  # Index of the most recently committed entry to the log list
        self.prevLogIndex = -1
        self.nextIndex = 0

    # _________________________________
    # --------- LOG METHODS -----------
    # =================================
    def appendEntryToLog(self, gamestate: GameState, term) -> None:
        """Adds a potential entry (i.e. client action and game response) to the local log list
        NOTE: This does not commit the entry!"""
        self.logList.append((gamestate, term))
        self.lastAppendedEntry += 1
        self.nextIndex += 1

    def commitEntryToLog(self) -> None:
        """Adds a confirmed entry (i.e. client action and game response) to the local log list
        NOTE: This is a commit and cannot be rolled back!"""
        # I don't know how we are going to demo this, but our commit is only recognized by this index number
        # If our item is committed this index gets incremented, this also only gets incremented when the leader
        # says so
        self.lastCommittedEntry += 1
    
    def appendEntriesToLog(self, partialLeaderLog):
        """ appends the missing entries into log"""
        for item in partialLeaderLog:
            self.appendEntryToLog(item[0], item[1])
        self.lastCommittedEntry = len(self.logList)
        self.lastAppendedEntry = len(self.logList)

    def getSubLog(self, startIndex):
        """ returns this list from the startIndex to the end of the list"""
        return self.logList[startIndex::]

    def removeItemsFromIndextoEnd(self, startIndex):
        """ removes all items from the index to the end of the list"""
        for i in range(startIndex, len(self.logList)):
            self.logList.__delitem__(i)

    def getTermAtIndex(self, index):
        """ returns the term of the entry at a given index """
        retVal = 0
        if len(self.logList) > 0 and index < len(self.logList):
            entryAtIndex = self.logList[index]
            retVal = entryAtIndex[1]
        return retVal

    def printLogEntries(self):
        """Prints all the committed log entries"""
        if len(self.logList) == 0:
            print("Log is empty!")
        else:
            for i in range(len(self.logList)):
                print("\n============ LOG ENTRY ============")
                print("Log Entry #" + str(i))
                print("Term #" + str(self.logList[i][1]))
                self.logList[i][0].printGameState()
                if i <= self.lastCommittedEntry:
                    print("STATUS IN LOG: Committed")
                else:
                    print("STATUS IN LOG: Appended")
