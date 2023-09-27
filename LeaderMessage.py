
class LeaderMessage:
    def __init__(self, currentTerm, entries, lastCommittedEntry, lastAppendedEntry, prevLogTerm, prevLogIndex, nextIndex):
        self.currentTerm = currentTerm
        self.entries = entries
        self.lastCommittedEntry = lastCommittedEntry
        self.lastAppendedEntry = lastAppendedEntry
        self.prevLogTerm = prevLogTerm
        self.prevLogIndex = prevLogIndex
        self.nextIndex = nextIndex
