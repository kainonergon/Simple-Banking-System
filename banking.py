import sys
import random
import sqlite3
from string import digits


class Banking:
    IIN = "400000"
    ACCOUNT_LEN = 9
    DATA_FILE = "card.s3db"

    def __init__(self):
        self.conn = sqlite3.connect(self.DATA_FILE)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.setup_database()
        self.account = None
        self.main_menu = {"1": ("Create an account", self.account_create),
                          "2": ("Log into account", self.account_login),
                          "0": ("Exit", self.bye)}
        self.account_menu = {"1": ("Balance", self.print_balance),
                             "2": ("Add income", self.add_income),
                             "3": ("Do transfer", self.do_transfer),
                             "4": ("Close account", self.account_close),
                             "5": ("Log out", self.account_logout),
                             "0": ("Exit", self.bye)}
        while True:
            self.open_menu(self.main_menu)

    def setup_database(self):
        sql = """CREATE TABLE IF NOT EXISTS card(
                id INTEGER PRIMARY KEY,
                number TEXT NOT NULL UNIQUE,
                pin TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 0
                );"""
        self.cur.execute(sql)
        self.conn.commit()

    def look_up_database(self, card_number) -> sqlite3.Row:
        sql = "SELECT pin, balance FROM card WHERE number = :number;"
        data = {"number": card_number}
        return self.cur.execute(sql, data).fetchone()

    def write_to_database(self, account, pin=None, amount=None, to_account=None, delete=False):
        if pin:
            sql = "INSERT INTO card (number, pin) VALUES (:number, :pin);"
            data = ({"number": account, "pin": pin},)
        elif delete:
            sql = "DELETE FROM card WHERE number = :number"
            data = ({"number": account},)
        elif to_account:
            sql = "UPDATE card SET balance = balance + :amount WHERE number = :number"
            data = ({"amount": -amount, "number": account},
                    {"amount": amount, "number": to_account})
        else:
            sql = "UPDATE card SET balance = balance + :amount WHERE number = :number"
            data = ({"amount": amount, "number": account},)
        self.cur.executemany(sql, data)
        self.conn.commit()

    @staticmethod
    def open_menu(menu):
        prompt = "".join((f"{i}. {menu[i][0]}\n" for i in menu))
        choice = input(prompt)
        print()
        if choice in menu:
            menu[choice][1]()

    def bye(self):
        self.conn.close()
        print("Bye!")
        sys.exit()

    def account_create(self):
        card_number = self.new_card_number()
        pin = "".join(random.choices(digits, k=4))
        self.write_to_database(card_number, pin=pin)
        print("Your card has been created")
        print(f"Your card number:\n{card_number}")
        print(f"Your card PIN:\n{pin}\n")

    def new_card_number(self) -> str:
        while True:
            account_number = "".join(random.choices(digits, k=self.ACCOUNT_LEN))
            card_number = "".join((self.IIN, account_number))
            card_number = "".join((card_number, Banking.luhn_add_digit(card_number)))
            if self.look_up_database(card_number) is None:
                return card_number

    def account_login(self):
        print("Enter your card number:")
        card_number = input()
        print("Enter your PIN:")
        pin = input()
        row = self.look_up_database(card_number)
        if row is None or pin != row['pin']:
            print("Wrong card number or PIN!\n")
            return
        self.account = card_number
        print("\nYou have successfully logged in!\n")
        while self.account:
            self.open_menu(self.account_menu)

    def print_balance(self):
        row = self.look_up_database(self.account)
        print(f"Balance: {row['balance']}\n")

    def add_income(self):
        amount = int(input("Enter income:\n"))
        if amount <= 0:
            print("Must be positive")
            return
        self.write_to_database(self.account, amount=amount)
        print("Income was added!\n")

    def do_transfer(self):
        print("Transfer")
        to_account = input("Enter card number:\n")
        if to_account == self.account:
            print("You can't transfer money to the same account!")
            return
        if not Banking.luhn_test(to_account):
            print("Probably you made a mistake in the card number. Please try again!")
            return
        if self.look_up_database(to_account) is None:
            print("Such a card does not exist.")
            return
        amount = int(input("Enter how much money you want to transfer:\n"))
        if amount <= 0:
            print("Must be positive")
            return
        if self.look_up_database(self.account)['balance'] < amount:
            print("Not enough money!")
            return
        self.write_to_database(self.account, amount=amount, to_account=to_account)
        print("Success!\n")

    def account_close(self):
        self.write_to_database(self.account, delete=True)
        self.account = None
        print("The account has been closed!\n")

    def account_logout(self):
        self.account = None
        print("Logged out!\n")

    @staticmethod
    def luhn_add_digit(number: str) -> str:
        luhn = (int(d) for d in number)
        luhn = (d if i % 2 else d * 2 + d * 2 // 10 for i, d in enumerate(luhn))
        return str(-sum(luhn) % 10)

    @staticmethod
    def luhn_test(number: str) -> bool:
        return Banking.luhn_add_digit(number) == '0'


if __name__ == '__main__':
    Banking()
