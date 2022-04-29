from time import time
from utility.printable import Printable


class Block(Printable):
    def __init__(self, index, previous_hash, transactions, proof_of_work, time=time()):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = time
        self.proof = proof_of_work

