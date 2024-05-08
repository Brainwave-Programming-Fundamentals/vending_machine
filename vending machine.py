from random import randint, choices
from string import digits
import pandas as pd
from faker import Faker  # 가짜 이름 라이브러리


class WithdrawError(Exception):  # 출금 에러 클래스
    def __init__(self, account, amount):
        self.account = account
        self.amount = amount

    def __str__(self):
        return f'insufficient balance: ' \
               f'balance is ￦{self.account.get_balance():,d} ' \
               f'but withdrawal amount is ￦{self.amount:,d}'


class PaymentError(Exception):
    def __init__(self, payment):
        self.payment = payment

    def __str__(self):
        return f'invalid payment method: {self.payment}'


class BankAccount:
    def __init__(self, name):
        self.__account_number = ''.join(choices(digits, k=13))
        self.__balance = 0  # 잔액
        self.name = name

    def __str__(self):
        return '이름: {:s}\n' \
               '계좌번호: {:0>4s}-{:s}-{:s}\n' \
               '잔액: ￦{:,d}'.format(
                self.name,
                self.__account_number[:-9],
                self.__account_number[-9:-7],
                self.__account_number[-7:],
                self.__balance)

    def get_balance(self):
        return self.__balance

    def deposit(self, amount):  # 입금
        self.__balance += amount

    def withdraw(self, amount):  # 출금
        if amount <= self.__balance:
            self.__balance -= amount
        else:
            raise WithdrawError(self, amount)


class Card:
    def __init__(self, account):
        self.__card_number = ''.join(choices(digits, k=16))
        self.__history = []  # 카드 사용 내역
        self.account = account  # 카드 소유주

    def __str__(self):
        return '카드번호: {}\n' \
               '↓ 소유주 정보 ↓\n' \
               '{}'.format(
                '-'.join([self.__card_number[i:i + 4] for i in range(0, 13, 4)]),
                self.account)


class VendingMachine:  # 자판기 클래스
    def __init__(self):
        item_list = [
            '글루텐-프리 에너지바',
            '글루텐-프리 어니언링',
            '글루텐-프리 크래커',
            '글루텐-프리 시리얼',
            '글루텐-프리 베이글',
            '글루텐-프리 감자칩',
            '글루텐-프리 쿠키',
            '할랄 소시지',
            '할랄 치킨',
            '할랄 케밥',
            '할랄 파이',
            '할랄 캔디'
        ]
        self.__items = pd.DataFrame(
            {item: [randint(10, 20), randint(7, 20) * 100] for item in item_list},
            index=['수량', '가격'])
        self.__items = self.__items.transpose()
        self.__moneybox = {
            10000: 0,
            5000: 0,
            1000: 100,
            500: 200,
            100: 500
        }

    def __str__(self):
        return str(self.__items)

    def buy(self):
        payment = input('결제 수단을 입력하세요. (현금 또는 카드): ')
        if payment == '현금':
            self.__buy_with_cash()
        elif payment == '카드':
            self.__buy_with_card()
        else:
            raise PaymentError(payment)

    def __buy_with_cash(self):
        raise NotImplementedError

    def __buy_with_card(self):
        raise NotImplementedError


card1 = Card(BankAccount(Faker('ko-KR').name()))
card1.account.deposit(randint(100, 999) * 1000)
print(card1)

vending_machine1 = VendingMachine()
print(vending_machine1)

vending_machine1.buy()
