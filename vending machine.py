from random import randint, choices
from string import digits
import pandas as pd
import re  # 정규 표현식 라이브러리
import pint  # 화폐단위 라이브러리
from faker import Faker  # 가짜 이름 라이브러리
from tabulate import tabulate  # 데이터프레임 가독성 향상 라이브러리


# 화폐단위 정의
currency_registry = pint.UnitRegistry()
currency_registry.define('USD = [currency]')  # 기준 단위
currency_registry.define('KRW = USD / 1368')
currency_registry.define('CNY = USD / 7.22')
USD = currency_registry.USD
KRW = currency_registry.KRW
CNY = currency_registry.CNY
# 임의로 추가 가능
#


class BankAccount:
    def __init__(self, name, unit: pint.Unit):
        self.__account_number = ''.join(choices(digits, k=13))
        self.__balance = 0 * unit  # 잔액 (화폐단위 포함)
        self.name = name

    def __str__(self):
        return '이름: {:s}\n' \
               '계좌번호: {:s}-**-***{:s}\n' \
               '잔액: {:,}'.format(
                self.name,
                self.__account_number[:-9],
                self.__account_number[-4:],
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
        self.account: BankAccount = account  # 카드 소유주

    def __str__(self):
        return '카드번호: {}\n' \
               '↓ 소유주 정보 ↓\n' \
               '{}'.format(
                '-'.join([self.__card_number[:4], '****', '****', self.__card_number[-4:]]),
                self.account)

    def pay(self, amount):
        self.account.withdraw(amount)


class WithdrawError(Exception):  # 출금 에러
    def __init__(self, account: BankAccount, amount):
        self.account: BankAccount = account
        self.amount = amount.to(account.get_balance().units)

    def __str__(self):
        return f'insufficient balance: ' \
               f'balance is {self.account.get_balance():,}, ' \
               f'but withdrawal amount is {self.amount:,}'


class OutOfStockError(Exception):  # 품절 에러
    def __init__(self, item=None):
        self.item = item

    def __str__(self):
        if self.item is None:
            return f'currently all out of stock'
        return f'{self.item} is currently out of stock'


class ItemError(Exception):
    def __init__(self, item):
        self.item = item

    def __str__(self):
        return f'non-existent item or ID: {self.item}'


class QuantityError(Exception):  # 수량 에러
    def __init__(self, quantity):
        self.quantity = quantity

    def __str__(self):
        return f'invalid quantity requested: {self.quantity}'


class OverStockError(Exception):  # 재고 초과 에러
    def __init__(self, item, stock, requested):
        self.item = item
        self.stock = stock  # 현재 재고
        self.requested = requested  # 요청 수량

    def __str__(self):
        return f'{self.item} only has {self.stock} in stock, ' \
               f'but {self.requested} was requested'


class PaymentError(Exception):
    def __init__(self, payment):
        self.payment = payment

    def __str__(self):
        return f'invalid payment method: {self.payment}'


class CurrencyError(Exception):
    def __init__(self, currency):
        self.currency = currency

    def __str__(self):
        return f'non-existent currency: {self.currency}원'


class VendingMachine:  # 자판기 클래스
    def __init__(self):
        item_list = [
            ['글루텐-프리 에너지바', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['글루텐-프리 어니언링', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['글루텐-프리 크래커', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['글루텐-프리 시리얼', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['글루텐-프리 베이글', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['글루텐-프리 감자칩', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['글루텐-프리 쿠키', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['할랄 소시지', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['할랄 치킨', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['할랄 케밥', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['할랄 파이', randint(0, 20), randint(5, 20) * 100 * KRW],
            ['할랄 캔디', randint(0, 20), randint(5, 20) * 100 * KRW]
        ]
        self.__items = pd.DataFrame(
            item_list,
            columns=['item', 'stock', 'price']).set_index('item')
        self.__moneybox = {  # 50000원, 50원, 10원은 취급하지 않음
            10000: 0,
            5000: 50,
            1000: 100,
            500: 200,
            100: 500
        }

    def __str__(self):
        return str(tabulate(
            self.__items.reset_index().rename(columns={'index': 'item'}),
            headers='keys', tablefmt='rst'))

    def is_out_of_stock(self, item=None):
        if item is None:
            return (self.__items['stock'] == 0).all()
        return self.__items.at[item, 'stock'] == 0

    def __insert_money(self, inserted_moneybox: dict):
        for currency, quantity in inserted_moneybox.items():
            if currency in self.__moneybox:
                self.__moneybox[currency] += quantity

    def __return_change(self, change):
        if change == 0:
            return

        return_moneybox = {}
        for currency in self.__moneybox:
            quantity = min(self.__moneybox[currency], change // currency)
            return_moneybox.update({currency: quantity})
            self.__moneybox[currency] -= quantity
            change -= currency * quantity
        self.__return_inserted_money(return_moneybox)

    @staticmethod
    def __return_inserted_money(return_moneybox: dict):
        changes = []
        for currency, quantity in return_moneybox.items():
            if 0 < quantity:
                if 1000 <= currency:
                    changes.append(f'{currency}원 {quantity}장')
                else:
                    changes.append(f'{currency}원 {quantity}개')
        if 0 < len(changes):
            print('반환됨: ' + ', '.join(changes))
        else:
            print('반환할 금액이 없습니다.')

    @staticmethod
    def __print_receipt(payment, shopping_dict, total_price, total_cash=None):
        if type(payment) == Card:
            raise NotImplementedError
        elif payment == '현금':
            raise NotImplementedError
        else:
            raise PaymentError(payment)

    def buy(self):
        print(self)
        if self.is_out_of_stock():
            raise OutOfStockError()

        shopping_dict = {}
        while True:
            print('구매할 상품의 번호 또는 상품명을 입력하세요.\n'
                  '아무것도 입력하지 않으면 결제 화면으로 이동합니다.: ', end='')
            item = input().strip()
            if item == '':
                break

            if item.isdigit() and 0 <= int(item) < self.__items.shape[0]:
                shopping_item = self.__items.index[int(item)]
            elif item in self.__items.index:
                shopping_item = item
            else:
                raise ItemError(item)

            if self.is_out_of_stock(shopping_item):
                raise OutOfStockError(shopping_item)

            print('선택한 상품의 구매 수량을 입력하세요.: ', end='')
            quantity = input().strip()
            if quantity.isdigit():
                quantity = int(quantity)
                if quantity <= 0:
                    raise QuantityError(quantity)
            else:
                raise QuantityError(quantity)

            if shopping_item in shopping_dict:
                shopping_dict[shopping_item] += quantity
            else:
                shopping_dict[shopping_item] = quantity

            if self.__items.at[shopping_item, 'stock'] < shopping_dict[shopping_item]:
                raise OverStockError(shopping_item,
                                     self.__items.at[shopping_item, 'stock'],
                                     shopping_dict[shopping_item])

        if shopping_dict == {}:
            print('결제할 상품이 없습니다.')
            return

        shopping_df = pd.DataFrame(
            [[item, quantity, quantity * self.__items.at[item, 'price']] for item, quantity in shopping_dict.items()],
            index=shopping_dict.keys(),
            columns=['item', 'quantity', 'price'])
        print(tabulate(shopping_df, headers='keys', tablefmt='rst', showindex=False))
        print(f'Total price: {sum(shopping_df["price"]):,}')
        print('결제 수단을 입력하세요. (카드 또는 현금): ', end='')
        payment = input().strip()
        if payment == '카드':
            self.__buy_with_card(shopping_dict, sum(shopping_df['price']))
        elif payment == '현금':
            self.__buy_with_cash(shopping_dict, sum(shopping_df['price']))
        else:
            raise PaymentError(payment)

    def __buy_with_cash(self, shopping_dict, total_price: pint.Quantity):
        total_price = total_price.magnitude
        inserted_moneybox = {  # 투입한 현금을 바로 self.__moneybox 에 넣지 않고 임시로 보관하는 딕셔너리
            50000: 0,
            10000: 0,
            5000: 0,
            1000: 0,
            500: 0,
            100: 0,
            50: 0,
            10: 0
        }

        # 현금 투입 처리
        print('현금을 투입하세요. 오만원, 오십원, 십원 권은 취급하지 않습니다.\n'
              '(ex. 5000원 1장, 500원 2개): ', end='')
        inserted_currency_list = list(map(str.strip, input().strip().split(',')))

        for i in range(len(inserted_currency_list)):
            inserted_currency = re.match(r'(\d+)원\s*(\d+)[개장]', inserted_currency_list[i])

            if inserted_currency is None:  # 입력 형식이 틀리면 에러
                raise SyntaxError(inserted_currency_list[i])

            currency = int(inserted_currency.group(1))
            quantity = int(inserted_currency.group(2))

            if currency not in inserted_moneybox:  # 존재하지 않는 화폐 입력시 에러 (ex. 2000원 1장)
                raise CurrencyError(currency)

            inserted_moneybox[currency] += quantity

        # 취급하지 않는 화폐 처리
        if 0 < inserted_moneybox[50000] or 0 < inserted_moneybox[50] or 0 < inserted_moneybox[10]:
            print('오만원, 오십원, 십원 권은 취급하지 않습니다. 투입한 모든 현금을 반환합니다.')
            self.__return_inserted_money(inserted_moneybox)
            return

        # 금액 부족 처리
        total_cash = sum([currency * quantity for currency, quantity in inserted_moneybox.items()])
        print(f'투입된 금액: {total_cash:,} KRW')
        if total_cash < total_price:
            print('금액이 부족합니다. 투입한 모든 현금을 반환합니다.')
            self.__return_inserted_money(inserted_moneybox)
            return

        # 정상적으로 현금이 투입되었다면 self.__moneybox 에 투입, 상품 지급, 거스름돈 반환
        self.__insert_money(inserted_moneybox)

        for item, quantity in shopping_dict.items():
            self.__items.at[item, 'stock'] -= quantity
        print('투출구에서 상품을 확인하세요.')
        self.__return_change(total_cash - total_price)

        # 영수증 출력
        print('영수증을 출력하시겠습니까? (y/n): ', end='')
        if input().strip().lower() == 'y':
            self.__print_receipt('현금', shopping_dict, total_price, total_cash)

    def __buy_with_card(self, shopping_dict, total_price: pint.Quantity):
        raise NotImplementedError


# 계좌 개설 및 카드 발급
card1 = Card(BankAccount(Faker('ko-KR').name(), KRW))
card1.account.deposit(randint(100, 999) * 1000 * KRW)
card2 = Card(BankAccount(Faker('en-US').name(), USD))
card2.account.deposit(randint(100, 999) * 1000 * KRW)
card3 = Card(BankAccount(Faker('zh-CN').name(), CNY))
card3.account.deposit(randint(100, 999) * 1000 * KRW)
print(card1, card2, card3, sep='\n\n', end='\n\n')

# 자판기 인스턴스 생성 및 실행
vending_machine1 = VendingMachine()
while True:
    vending_machine1.buy()
