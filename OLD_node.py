from blockchain import Blockchain

from utility.verification import Verification
from wallet import Wallet


class Node:
    def __init__(self):
        # self.id = str(uuid4())
        self.wallet = Wallet()
        self.wallet.create_keys()
        self.blockchain = Blockchain(self.wallet.public_key)

    def get_transaction_value(self):
        """ Returns the input of the user (a new transaction value) as a tuple. """
        recipient = input('Enter the recipient of the transaction: ')
        amount = float(input('Your transaction amount please: '))
        return recipient, amount

    def print_blockchain_elements(self):
        for block in self.blockchain.chain:
            print('Outputting a block')
            print(block)
        else:
            print('-' * 20)

    def get_user_choice(self):
        user_input = input('Your choice: ')
        return user_input

    def listen_for_input(self):
        waiting_for_input = True

        while waiting_for_input:
            print('Please choose:')
            print('1: Add a new transaction value')
            print('2: Mine a new block')
            print('3: Output the blockchain blocks')
            print('4: Manipulate the chain')
            print('5: Check transaction validity')
            print('6: Create a wallet')
            print('7: Load a wallet')
            print('8: Save keys')
            print('9: Quit')
            user_choice = self.get_user_choice()
            if user_choice == '1':
                data = self.get_transaction_value()
                recipient, amount = data
                signature = self.wallet.sign_transaction(self.wallet.public_key, recipient, amount)
                if self.blockchain.add_transaction(recipient, self.wallet, signature, amount):
                    print('Added transaction!')
                else:
                    print('Transaction failed')
                print(self.blockchain.get_open_transactions())
            elif user_choice == '2':
                if not self.blockchain.mine_block():
                    print('Mining failed. Got no wallet?')
            elif user_choice == '3':
                self.print_blockchain_elements()
            elif user_choice == '4':
                if len(self.blockchain.chain) >= 1:
                    self.blockchain.chain[0] = {'previousHash': '', 'index': 0,
                                                'transactions': [
                                                    {'sender': 'Chris', 'recipient': 'Max', 'amount': 100}]}
            elif user_choice == '5':
                if Verification.verify_transactions(self.blockchain.get_open_transactions(), self.blockchain.get_balance):
                    print('All transactions are valid!')
                else:
                    print('There are invalid transactions.')
            elif user_choice == '6':
                self.wallet.create_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            elif user_choice == '7':
                self.wallet.load_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            elif user_choice == '8':
                self.wallet.save_keys()
            elif user_choice == '9':
                waiting_for_input = False
            else:
                print('Invalid input')
            print('Choice registered!')
            if not Verification.verify_chain(self.blockchain.chain):
                print('Invalid blockchain!')
                break
            print('Balance of {}: {:6.2f}'.format(self.wallet.public_key, self.blockchain.get_balance()))
        else:
            print('User left')

        print('Done!')


if __name__ == '__main__':
    node = Node()
    node.listen_for_input()
