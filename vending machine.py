from datetime import datetime
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


class BankAccount:
    def __init__(self, name, unit: pint.Unit):
        self.__account_number = ''.join(choices(digits, k=13))
        self.__balance = 0 * unit  # 잔액 (화폐단위 포함)
        self.__name = name

    def __str__(self):
        return f'이름: {self.__name}\n' \
               f'계좌번호: {self.__account_number[:-9]}-**-***{self.__account_number[-4:]}\n' \
               f'잔액: {self.__balance:,}'

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
    def __init__(self, account: BankAccount):
        self.__card_number = ''.join(choices(digits, k=16))
        self.account = account  # 카드 소유주

    def __str__(self):
        return f'카드번호: {self.__card_number[:4]}-****-****-{self.__card_number[-4:]}\n' \
               f'↓ 소유주 정보 ↓\n' \
               f'{self.account}'

    def get_card_number(self):
        return f'{self.__card_number[:4]}-****-****-{self.__card_number[-4:]}'

    def get_balance(self):
        return self.account.get_balance()

    def pay(self, amount, to: BankAccount = None):
        self.account.withdraw(amount)
        if to is not None:
            to.deposit(amount)


class WithdrawError(Exception):  # 출금 에러
    def __init__(self, account: BankAccount, amount):
        self.account = account
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


class OverStockError(Exception):  # 요청 수량 초과 에러
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


class DenominationError(Exception):
    def __init__(self, denomination):
        self.denomination = denomination

    def __str__(self):
        return f'non-existent denomination: {self.denomination}원'


class VendingMachine:  # 자판기 클래스
    def __init__(self, card_list):
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
            5000: 0,
            1000: 100,
            500: 200,
            100: 1000
        }
        self.__card_list = card_list

    def __str__(self):
        return str(tabulate(
            self.__items.reset_index().rename(columns={'index': 'item'}),
            headers='keys', tablefmt='rounded_outline'))

    def is_out_of_stock(self, item=None):
        if item is None:
            return all(self.__items['stock'] == 0)
        return self.__items.at[item, 'stock'] == 0

    def is_cash_payment_possible(self):
        for denomination in [1000, 500, 100]:
            if self.__moneybox[denomination] < 10:
                return False
        return True

    def __insert_money(self, moneybox: dict):
        for denomination, quantity in moneybox.items():
            if denomination in self.__moneybox:
                self.__moneybox[denomination] += quantity

    def __return_change(self, change):
        if change == 0:
            return

        return_moneybox = {}
        for denomination in [1000, 500, 100]:
            quantity = min(self.__moneybox[denomination], change // denomination)
            return_moneybox.update({denomination: quantity})
            self.__moneybox[denomination] -= quantity
            change -= denomination * quantity
        self.__return_money(return_moneybox)

    @staticmethod
    def __return_money(return_moneybox: dict):
        changes = []
        for denomination, quantity in return_moneybox.items():
            if 0 < quantity:
                if 1000 <= denomination:
                    changes.append(f'{denomination}원 {quantity}장')
                else:
                    changes.append(f'{denomination}원 {quantity}개')
        if 0 < len(changes):
            print('반환됨: ' + ', '.join(changes))
        else:
            print('반환할 금액이 없습니다.')

    @staticmethod
    def __print_receipt(payment, shopping_df: pd.DataFrame, total_price: int, total_cash: int = None):
        shopping_df.reset_index(inplace=True)
        shopping_df.rename(columns={'item': '상품명', 'price': '단가', 'amount': '수량'}, inplace=True)
        shopping_df.set_index('상품명', inplace=True)
        shopping_df['금액'] = shopping_df['단가'] * shopping_df['수량']
        receipt = str(tabulate(shopping_df, headers='keys', tablefmt='rst', showindex=True))
        width = receipt.find('\n')
        if type(payment) == Card:
            print(f'\n{"구매 영수증":=^{width - 5}}\n'
                  f'주문일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S(%a)")}\n'
                  f'결제수단: 카드\n'
                  f'{receipt}\n\n'
                  f'합    계: {total_price:6,}\n'
                  f'받을금액: {total_price:6,}\n'
                  f'받은금액: {total_price:6,}\n'
                  f'{"=" * width}')
        elif payment == '현금':
            print(f'\n{"구매 영수증":=^{width - 5}}\n'
                  f'주문일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S(%a)")}\n'
                  f'결제수단: 현금\n'
                  f'{receipt}\n\n'
                  f'합    계: {total_price:6,}\n'
                  f'받을금액: {total_price:6,}\n'
                  f'받은금액: {total_cash:6,}\n'
                  f'거스름돈: {total_cash - total_price:6,}\n'
                  f'{"=" * width}')
        else:
            raise PaymentError(payment)

    def buy(self):
        print('\n' + str(self))
        if self.is_out_of_stock():
            raise OutOfStockError()

        if not self.is_cash_payment_possible():
            print('※ 현재 카드 결제만 가능합니다. ※')

        shopping_dict = {}
        while True:
            print('구매할 상품의 번호 또는 상품명을 입력하세요.\n'
                  '아무것도 입력하지 않으면 결제 화면으로 이동합니다.: ', end='')
            item = input().strip()
            if item == '':
                break

            if item.isdigit() and 0 <= int(item) < len(self.__items):
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
            print('\n결제할 상품이 없습니다.')
            return

        shopping_df = pd.DataFrame(
            [[item, quantity, quantity * self.__items.at[item, 'price']] for item, quantity in shopping_dict.items()],
            index=shopping_dict.keys(),
            columns=['item', 'quantity', 'price'])
        print('\n↓ 선택한 상품 목록 ↓')
        print(tabulate(shopping_df, headers='keys', tablefmt='rounded_outline', showindex=False))
        print(f'합계: {sum(shopping_df["price"]):,}')

        if not self.is_cash_payment_possible():
            print('\n※ 현재 카드 결제만 가능합니다. ※')
            self.__buy_with_card(shopping_dict, sum(shopping_df['price']))
            return

        print('\n결제 수단을 입력하세요. (카드 또는 현금): ', end='')
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
        print('\n현금을 투입하세요. 오만원, 오십원, 십원 권은 취급하지 않습니다.\n'
              '(ex. 5000원 1장, 500원 2개): ', end='')
        inserted_denomination_list = list(map(str.strip, input().strip().split(',')))
        for i in range(len(inserted_denomination_list)):
            inserted_denomination = re.match(r'(\d+)원\s*(\d+)[개장]', inserted_denomination_list[i])

            if inserted_denomination is None:  # 입력 형식이 틀리면 에러
                raise SyntaxError(inserted_denomination_list[i])

            denomination = int(inserted_denomination.group(1))
            quantity = int(inserted_denomination.group(2))

            if denomination not in inserted_moneybox:  # 존재하지 않는 화폐 입력시 에러 (ex. 2000원 1장)
                raise DenominationError(denomination)

            inserted_moneybox[denomination] += quantity

        # 취급하지 않는 화폐 처리
        if any([inserted_moneybox[denomination] for denomination in [50000, 500, 100, 50, 10]]):
            print('\n오만원 권과 동전은 취급하지 않습니다. 투입한 모든 현금을 반환합니다.')
            self.__return_money(inserted_moneybox)
            return

        # 금액 부족 처리
        total_cash = sum([denomination * quantity for denomination, quantity in inserted_moneybox.items()])
        print(f'\n투입된 금액: {total_cash:,} KRW')
        if total_cash < total_price:
            print('금액이 부족합니다. 투입한 모든 현금을 반환합니다.')
            self.__return_money(inserted_moneybox)
            return

        # 정상적으로 현금이 투입되었다면 self.__moneybox 에 투입, 상품 지급, 거스름돈 반환
        self.__insert_money(inserted_moneybox)
        for item, quantity in shopping_dict.items():
            self.__items.at[item, 'stock'] -= quantity
        print('\n투출구에서 상품을 확인하세요.\n↓ 투출구 ↓')
        print(tabulate(shopping_dict.items(), headers=['품목', '수량'], tablefmt='rounded_outline', showindex=False))
        self.__return_change(total_cash - total_price)

        # 영수증 출력
        print('\n영수증을 출력하시겠습니까? (y/n): ', end='')
        if input().strip().lower() == 'y':
            shopping_df = self.__items.loc[shopping_dict.keys(), ['price']]
            shopping_df.insert(0, 'amount', shopping_dict.values())
            self.__print_receipt('현금', shopping_df, total_price, total_cash)

    def __buy_with_card(self, shopping_dict, total_price: pint.Quantity):
        print('\n↓ 사용 가능한 카드 목록 ↓')
        print(tabulate(zip(map(Card.get_card_number, self.__card_list), map(Card.get_balance, self.__card_list)),
                       headers=['카드번호', '잔액'], showindex=True, tablefmt='rounded_outline'))
        print(f'결제할 카드를 선택하세요. (0 ~ {len(self.__card_list) - 1}): ', end='')
        idx = input()
        if idx.isdigit() and 0 <= int(idx) < len(self.__card_list):
            payment_card = self.__card_list[int(idx)]
            try:
                payment_card.pay(total_price)
            except WithdrawError:
                print('잔액이 부족합니다.')
            else:
                for item, quantity in shopping_dict.items():
                    self.__items.at[item, 'stock'] -= quantity
                print('\n투출구에서 상품을 확인하세요.\n↓ 투출구 ↓')
                print(tabulate(shopping_dict.items(), headers=['품목', '수량'], tablefmt='rounded_outline'))

                # 영수증 출력
                print('\n영수증을 출력하시겠습니까? (y/n): ', end='')
                if input().strip().lower() == 'y':
                    shopping_df = self.__items.loc[shopping_dict.keys(), ['price']]
                    shopping_df.insert(0, 'amount', shopping_dict.values())
                    self.__print_receipt(payment_card, shopping_df, total_price.magnitude)
        else:
            raise ItemError(idx)

    def admin_login(self):
        print('\n관리자 로그인\n'
              '비밀번호를 입력하세요.: ', end='')
        password = input()  # 비밀번호이므로 .strip() 사용 X
        if password == 'admin':  # 관리자 비밀번호는 'admin' 으로 설정
            self.__admin_menu()
        else:
            print('\n비밀번호가 일치하지 않습니다.')

    def __admin_menu(self):
        while True:
            print('\n1. 새로운 상품 추가\n'
                  '2. 기존 상품 삭제\n'
                  '3. 재고 관리\n'
                  '4. 가격 변경\n'
                  '5. 현금 수거\n'
                  '6. 종료\n'
                  '사용할 기능을 선택하세요 (1 ~ 6): ', end='')

            choice = input().strip()

            if choice == '1':
                self.__add_new_item()
            elif choice == '2':
                self.__remove_item()
            elif choice == '3':
                self.__restock_item()
            elif choice == '4':
                self.__update_price()
            elif choice == '5':
                self.__restock_moneybox()
            elif choice == '6':
                break
            else:
                print('\n올바른 기능을 입력해주세요.')

    def __add_new_item(self):
        if 20 <= len(self.__items):
            print('\n더 이상 상품을 추가할 수 없습니다. 기존 상품 삭제 후 이용해주세요.')
            return

        print('\n추가할 상품명을 입력하세요.\n'
              '아무것도 입력하지 않으면 관리자 메뉴로 돌아갑니다.: ', end='')
        item = input().strip()
        if item == '':
            return

        if item in self.__items.index:
            print('\n이미 존재하는 상품입니다. 동일한 상품을 추가하려는 경우 다른 이름을 사용해주세요.')
            return

        print('해당 상품의 추가 수량을 입력하세요.\n'
              '각 상품은 최대 20개까지 투입 가능합니다.: ', end='')
        quantity = input().strip()
        if quantity.isdigit() and int(quantity) <= 20:
            quantity = int(quantity)
        else:
            raise QuantityError(quantity)

        print('해당 상품의 판매 가격을 입력하세요. (ex. 2200원): ', end='')
        input_price = input().strip()
        price = re.match(r'(\d+)원', input_price)

        if price is None:  # 입력 형식이 틀리면 에러
            raise SyntaxError(input_price)

        price = int(price.group(1))

        new_df = pd.DataFrame([[item, quantity, price * KRW]], columns=['item', 'stock', 'price']).set_index('item')
        self.__items = pd.concat([self.__items, new_df])
        # self.__items.loc[item] = [quantity, price * KRW] 로 변경 가능하나, Pint 라이브러리 관련 경고 문구가 출력됨

        print(f'\n{item} {quantity}개가 추가되었습니다.')

    def __remove_item(self):
        print('\n' + str(self))
        print('삭제할 상품의 번호 또는 상품명을 입력하세요.\n'
              '아무것도 입력하지 않으면 관리자 메뉴로 돌아갑니다.: ', end='')
        item = input().strip()
        if item == '':
            return

        if item.isdigit() and 0 <= int(item) < len(self.__items):
            item = self.__items.index[int(item)]
        elif item not in self.__items.index:
            raise ItemError(item)

        print(f'\n{item} 품목이 삭제되었습니다.')
        self.__items.drop(index=item, inplace=True)

    def __restock_item(self):
        print('\n' + str(self))
        print('재고를 보충할 상품의 번호 또는 상품명을 입력하세요.\n'
              '아무것도 입력하지 않으면 관리자 메뉴로 돌아갑니다.: ', end='')
        item = input().strip()
        if item == '':
            return

        if item.isdigit() and 0 <= int(item) < len(self.__items):
            item = self.__items.index[int(item)]
        elif item not in self.__items.index:
            raise ItemError(item)

        if self.__items.at[item, 'stock'] == 20:
            print('\n해당 상품은 보충할 필요가 없습니다.')
            return

        print(f'선택한 상품의 보충 수량을 입력하세요.\n'
              f'해당 상품은 최대 {20 - self.__items.at[item, "stock"]}개까지 더 보충 가능합니다.: ', end='')
        quantity = input().strip()
        if not quantity.isdigit() or 20 < self.__items.at[item, 'stock'] + int(quantity):
            raise QuantityError(quantity)

        self.__items.at[item, 'stock'] += int(quantity)
        print(f'\n{item} {quantity}개가 추가되었습니다.')

    def __update_price(self):
        print('\n' + str(self))
        print('가격을 변경할 상품의 번호 또는 상품명을 입력하세요.\n'
              '아무것도 입력하지 않으면 관리자 메뉴로 돌아갑니다.: ', end='')
        item = input().strip()
        if item == '':
            return

        if item.isdigit() and 0 <= int(item) < len(self.__items):
            item = self.__items.index[int(item)]
        elif item not in self.__items.index:
            raise ItemError(item)

        print(f'{item}의 새로운 가격을 입력하세요. (ex. 2200원): ', end='')
        input_price = input().strip()
        price = re.match(r'(\d+)원', input_price)

        if price is None:  # 입력 형식이 틀리면 에러
            raise SyntaxError(input_price)

        price = int(price.group(1))

        print(f'\n{item}의 가격이 {price}원으로 변경되었습니다.')
        self.__items.at[item, 'price'] = price * KRW

    def __restock_moneybox(self):
        return_moneybox = {}
        for denomination in [10000, 5000]:  # 받기만 가능한 10000원, 5000원은 수거
            return_moneybox[denomination] = self.__moneybox[denomination]
            self.__moneybox[denomination] = 0

        for denomination, limit in zip([1000, 500, 100], [100, 200, 1000]):
            if limit < self.__moneybox[denomination]:
                return_moneybox[denomination] = self.__moneybox[denomination] - limit
                self.__moneybox[denomination] = limit
            else:
                print(f'{denomination}원 지폐 {limit - self.__moneybox[denomination]}장 보충되었습니다.'
                      if denomination == 1000 else
                      f'{denomination}원 동전 {limit - self.__moneybox[denomination]}개 보충되었습니다.')
                self.__moneybox[denomination] = limit
        self.__return_money(return_moneybox)


# 계좌 개설 및 카드 발급
cards = []
for _ in range(2):
    cards.append(Card(BankAccount(Faker('ko-KR').name(), KRW)))
    cards[-1].account.deposit(randint(100, 999) * 1000 * KRW)
    cards.append(Card(BankAccount(Faker('en-US').name(), USD)))
    cards[-1].account.deposit(randint(100, 999) * 1000 * KRW)
    cards.append(Card(BankAccount(Faker('zh-CN').name(), CNY)))
    cards[-1].account.deposit(randint(100, 999) * 1000 * KRW)
cards.append(Card(BankAccount(Faker('ko-KR').name(), KRW)))
cards.append(Card(BankAccount(Faker('en-US').name(), USD)))
cards.append(Card(BankAccount(Faker('zh-CN').name(), CNY)))

# 자판기 인스턴스 생성 및 실행
vending_machine1 = VendingMachine(cards)
while True:
    vending_machine1.buy()
    vending_machine1.admin_login()  # ← 테스트용 코드, 사용자 인터페이스 생기면 마우스 클릭 등으로 실행하면 좋을 듯
