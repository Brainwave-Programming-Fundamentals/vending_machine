from random import randint, choices
from string import digits
import pandas as pd
from faker import Faker  # 가짜 이름 라이브러리

class Empty(Exception): #재고 비어있으면 발생
    def __init__(self,items):
        self.items=items
        
    def __str__(self):
        return f"our vending maching is currently out of stock\n{self.items}"

class Outofstock(Exception): #제고가 원하는 품목의 수량보다 적으면 발생
    def __init__(self,item_name,input_size,available):
        self.item_name=item_name
        self.input_size=input_size
        self.available=available
    def __str__(self):
        return f"requested quantity {self.input_size} of {self.item_name}\
            exceeds available stock{self.available}"


class WithdrawError(Exception):  # 출금 에러 클래스
    def __init__(self, account, amount):
        self.account = account
        self.amount = amount

    def __str__(self):
        return f'insufficient balance: ' \
               f'balance is ￦{self.account.get_balance():,d} ' \
               f'but withdrawal amount is ￦{self.amount:,d}'

class WithdrawErrorUS(Exception):  # 추가
    def __init__(self, account, amount):
        self.account = account
        self.amount = amount

    def __str__(self):
        return f'insufficient balance: ' \
               f'balance is ${self.account.get_balance():,d} ' \
               f'but withdrawal amount is ${self.amount:,d}'
               
class WithdrawErrorCN(Exception):  # 추가
    def __init__(self, account, amount):
        self.account = account
        self.amount = amount

    def __str__(self):
        return f'insufficient balance: ' \
               f'balance is ¥{self.account.get_balance():,d} ' \
               f'but withdrawal amount is ¥{self.amount:,d}'



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
class BankAccountUS:   #추가
    def __init__(self, name):
        self.__account_number = ''.join(choices(digits, k=13))
        self.__balance = 0  # 잔액
        self.name = name

    def __str__(self):
        return 'name: {:s}\n' \
               'account number: {:0>4s}-{:s}-{:s}\n' \
               'balance: ${:,d}'.format(
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
            raise WithdrawErrorUS(self, amount)
        
class BankAccountCN:  #추가
    def __init__(self, name):
        self.__account_number = ''.join(choices(digits, k=13))
        self.__balance = 0  # 잔액
        self.name = name

    def __str__(self):
        return '名字: {:s}\n' \
               '账号: {:0>4s}-{:s}-{:s}\n' \
               '余额: ¥{:,d}'.format(
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
            raise WithdrawErrorCN(self, amount)


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
    def add_history(self,description,amount): #건호 수정
        self.__history.append([description,amount])
    
    def get_history(self): #건호 수정
        return self.__history
    




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
            {item: [randint(10,20), randint(7, 20) * 100] for item in item_list},
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
    
    def __inventory_management(self,item_name,item_quantity): #재고 관리
        self.__items.at[item_name,"수량"]-=item_quantity
        
    def is_empty(self): #모두 비어있는지 확인
        return (self.__items["수량"]==0).all()
    def item_empty(self,item_name):
        return self.__items.at[item_name,"수량"]==0
        

    def buy(self,card): #건호 수정
        if self.is_empty():
            raise Empty(self.__items)
        
        item_index=int(input("사고 싶은 품목을 고르시오."))# 품목 ID 
        item_quantity=int(input("사고 싶은 품목의 개수를 고르시오"))# 품목 사고 싶은 개수
        payment = input('결제 수단을 입력하세요. (현금 또는 카드): ')
        
        item_name=self.__items.index[item_index] #인덱스로 접근
        quantity=self.__items.at[item_name,"수량"] #객체의 수량 접근
        
        if item_quantity>quantity: #수량이 더 많으면 error 발생
            raise Outofstock(item_name,item_quantity,quantity)
        
        self.__inventory_management(item_name,item_quantity)
        
        
        price=self.__items.at[item_name,"가격"] # 객체의 가격 접근
        
        # 카드, 해외 카드 혹은 현금 접근
        if payment == '현금':
            self.__buy_with_cash(card,price,item_quantity)
        elif payment == '국내카드':
            self.__buy_with_dosmetic_card(card,price,item_quantity)
        elif payment=='미국카드':
            self.__buy_with_USD_card(card,price,item_quantity)
        elif payment=='중국카드':
            self.__buy_with_CNY_card(card,price,item_quantity)
        else:
            raise PaymentError(payment)

    def __buy_with_cash(self):
        

    def __buy_with_dosmetic_card(self,card,price,quantity):
        amount=quantity*price
        card.account.withdraw(amount)
        card.add_history("vending_machine1",amount)
        print(card.get_history())
        print(card.account.get_balance())
        
        
    def __buy_with_USD_card(self,card,price,quantity):#외국인 경향 상품이기 때문에 해외카드 적용
        price/=1300
        price=round(price,2)
        amount=quantity*price
        card.account.withdraw(amount)
        card.add_history("vending_machine1",amount)
        print(card.get_history())
        print(card.account.get_balance())
        
        
    def __buy_with_CNY_card(self,card,price,quantity):#외국인 경향 상품이기 때문에 해외카드 적용
        price/=185
        price=round(price,2)
        amount=quantity*price
        card.account.withdraw(amount)
        card.add_history("vending_machine1",amount)
        print(card.get_history())
        print(card.account.get_balance())
        


card1 = Card(BankAccount(Faker('ko-KR').name()))
card2= Card(BankAccountUS(Faker("en_US").name()))
card3 = Card(BankAccountCN(Faker("zh_CN").name()))
card1.account.deposit(randint(100, 999) * 1000)
print(card1)
card2.account.deposit(randint(100,999))
print(card2)
card3.account.deposit(randint(100,999)*100)
print(card3)


vending_machine1 = VendingMachine()
print(vending_machine1)

vending_machine1.buy(card1)
vending_machine1.buy(card2)
vending_machine1.buy(card3)
print(vending_machine1)

