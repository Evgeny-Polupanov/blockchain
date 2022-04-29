from functools import reduce
import json
import requests

from block import Block
from transaction import Transaction

from utility.hash_util import hash_block

from utility.verification import Verification
from wallet import Wallet

MINING_REWARD = 10

print(__name__)


class Blockchain:
    def __init__(self, public_key, node_id):
        genesis_block = Block(0, '', [], 100, 0)
        self.chain = [genesis_block]
        self.__open_transactions = []
        self.public_key = public_key
        self.__peer_nodes = set()
        self.node_id = node_id
        self.resolve_conflicts = False
        self.load_data()

    @property
    def chain(self):
        return self.__chain[:]

    @chain.setter
    def chain(self, value):
        self.__chain = value

    def get_open_transactions(self):
        return self.__open_transactions[:]

    def load_data(self):
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as file:
                file_content = file.readlines()
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                for block in blockchain:
                    processed_transactions = [
                        Transaction(transaction['sender'], transaction['recipient'], transaction['signature'],
                                    transaction['amount']) for
                        transaction
                        in block['transactions']]
                    updated_block = Block(block['index'], block['previous_hash'], processed_transactions,
                                          block['proof'],
                                          block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain
                open_transactions = json.loads(file_content[1][:-1])
                updated_transactions = []
                for transaction in open_transactions:
                    updated_transaction = Transaction(transaction['sender'], transaction['recipient'],
                                                      transaction['signature'],
                                                      transaction['amount'])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):
            print('Handled exception')
        finally:
            print('Cleanup')

    def save_data(self):
        try:
            with open('blockchain{}.txt'.format(self.node_id), mode='w') as file:
                savable_chain = [block.__dict__ for block in
                                 [Block(block_element.index, block_element.previous_hash,
                                        [transaction.__dict__ for transaction in
                                         block_element.transactions],
                                        block_element.proof, block_element.timestamp) for
                                  block_element in self.__chain]]
                file.write(json.dumps(savable_chain))
                file.write('\n')
                savable_transactions = [transaction.__dict__.copy() for transaction in self.__open_transactions]
                file.write(json.dumps(savable_transactions))
                file.write('\n')
                file.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving failed.')

    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0

        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1

        return proof

    def get_balance(self, sender=None):
        if sender is None:
            if self.public_key is None:
                return None
            participant = self.public_key
        else:
            participant = sender
        sender = [[transaction.amount for transaction in block.transactions if transaction.sender == participant]
                  for block in self.__chain]
        open_transaction_sender = [transaction.amount for transaction in self.__open_transactions if
                                   transaction.sender == participant]
        sender.append(open_transaction_sender)
        sent_amount = reduce(
            lambda transaction_sum, transaction_amount: transaction_sum + sum(transaction_amount) if len(
                transaction_amount) > 0 else transaction_sum + 0,
            sender, 0)
        recipient = [
            [transaction.amount for transaction in block.transactions if transaction.recipient == participant]
            for block in self.__chain]
        received_amount = reduce(
            lambda transaction_sum, transaction_amount: transaction_sum + sum(transaction_amount) if len(
                transaction_amount) > 0 else transaction_sum + 0, recipient, 0)
        return received_amount - sent_amount

    def get_last_blockchain_value(self):
        """ Returns the last value of the current blockchain. """
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def add_transaction(self, recipient, sender, signature, amount=1.0, is_receiving=False):
        """ Append a new value as well as the last blockchain value to the blockchain.

        Arguments:
            :recipient: The recipient of the coins
            :amount: The amount of coins sent with the transaction (default = 1.0 coin)
            :sender: The sender of the coins.
        """
        transaction = Transaction(sender, recipient, signature, amount)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = 'https://{}/broadcast-transaction'.format(node)
                    try:
                        response = requests.post(url,
                                                 json={'sender': sender, 'recipient': recipient, 'amount': amount,
                                                       'signature': signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolving.')
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False

    def mine_block(self):
        if self.public_key is None:
            return None
        last_block = self.__chain[-1]
        hash_of_block = hash_block(last_block)
        proof = self.proof_of_work()
        reward_transaction = Transaction('MINING', self.public_key, '', MINING_REWARD)
        copied_transactions = self.__open_transactions[:]
        for transaction in copied_transactions:
            if not Wallet.verify_transaction(transaction):
                return None
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hash_of_block, copied_transactions, proof)
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        for node in self.__peer_nodes:
            url = 'https://{}/broadcast-block'.format(node)
            converted_block = block.__dict__.copy()
            converted_block['transactions'] = [transaction.__dict__ for transaction in converted_block['transactions']]
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving.')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self, block):
        transactions = [Transaction(transaction['sender'], transaction['recipient'], transaction['signature'],
                                    transaction['amount']) for transaction in block['transactions']]
        proof_is_valid = Verification.valid_proof(transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        converted_block = Block(block['index'], block['previous_hash'], transactions, block['proof'],
                                block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]
        for incoming_transaction in block['transactions']:
            for open_transaction in stored_transactions:
                if open_transaction.sender == incoming_transaction['sender'] and open_transaction.recipient == \
                        incoming_transaction['recipient'] and open_transaction.amount == \
                        incoming_transaction['amount'] and open_transaction.signature == \
                        incoming_transaction['signature']:
                    try:
                        self.__open_transactions.remove(open_transaction)
                    except ValueError:
                        print('Item was already removed.')

        self.save_data()
        return True

    def resolve(self):
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = 'https://{}/chain'.format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'], block['previous_hash'], [
                    Transaction(transaction['sender'], transaction['recipient'], transaction['signature'],
                                transaction['amount']) for transaction in block['transactions']], block['proof'],
                                    block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(self.chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

    def add_peer_node(self, node):
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        return list(self.__peer_nodes)
