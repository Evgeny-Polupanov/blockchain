from utility.hash_util import hash_block, hash_string_256
from wallet import Wallet


class Verification:
    @classmethod
    def verify_chain(cls, blockchain):
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previousHash != hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(block.transactions[:-1], block.previousHash, block.proof):
                print('The proof of work is invalid.')
                return False
        return True

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        return all([cls.verify_transaction(transaction, get_balance, False) for transaction in open_transactions])

    @staticmethod
    def verify_transaction(transaction, get_balance, check_funds=True):
        if check_funds:
            sender_balance = get_balance()
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)
        else:
            return Wallet.verify_transaction(transaction)

    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        guess = (str([transaction.to_ordered_dict() for transaction in transactions]) + str(last_hash) + str(
            proof)).encode()
        guess_hash = hash_string_256(guess)

        return guess_hash[0:2] == '00'
