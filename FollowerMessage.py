
class FollowerMessage:
    def __init__(self, currentTerm, responseToLeader, lastCommittedIndex, nextIndex):
        self.currentTerm = currentTerm
        self.response = responseToLeader
        self.lastCommittedIndex = lastCommittedIndex
        self.nextIndex = nextIndex
