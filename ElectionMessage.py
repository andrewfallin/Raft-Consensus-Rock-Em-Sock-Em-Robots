
class ElectionMessage:
    def __init__(self, eid, currentTerm, lastLogIndex, lastLogTerm):
        self.eid = eid
        self.currentTerm = currentTerm
        self.lastLogIndex = lastLogIndex
        self.lastLogTems = lastLogTerm
