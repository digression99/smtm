import copy
import requests
from .date_converter import DateConverter
from .log_manager import LogManager

class VirtualMarket:
    URL = 'https://api.upbit.com/v1/candles/minutes/1'
    QUERY_STRING = { 'market': 'KRW-BTC', 'to': '2020-04-30 00:00:00'}

    def __init__(self):
        self.logger = LogManager.get_logger(__class__.__name__)
        self.is_initialized = False
        self.data = None
        self.turn_count = 0
        self.balance = 0
        self.commission_ratio = 0.0005
        self.asset = {}

    def initialize(self, end=None, count=100, budget=0):
        if self.is_initialized:
            return
        query_string = copy.deepcopy(self.QUERY_STRING)
        query_string['count'] = count
        
        try:
            response = requests.get(self.URL, params=query_string)
            response.raise_for_status()

            self.data = response.json()
            self.data.reverse()
            self.balance = budget
            self.is_initialized = True
            self.logger.debug(f"Virtual Market is initialized end: {end}, count: {count}")
        except ValueError as err:
            self.logger.error('invalid data from server')
            raise UserWarning('fail to get data from server') from err
        except requests.exceptions.HTTPError as err:
            self.logger.error(err)
            raise UserWarning('fail to get data from server') from err
        except requests.exceptions.RequestException as err:
            self.logger.error(err)
            raise UserWarning('fail to get data from server') from err

    def get_balance(self):
        asset_info = { 'balance': self.balance }
        quote = None
        try:
            quote = {
                    self.data[self.turn_count]['market']: self.data[self.turn_count]['trade_price']
                    }
            for name, item in self.asset.items():
                self.logger.debug(f"asset item: {name}, item price: {item[0]}, amount: {item[1]}")
        except (KeyError, IndexError) as msg:
            self.logger.error(f"invalid trading data {msg}")
            return None

        asset_info['asset'] = self.asset
        asset_info['quote'] = quote
        asset_info['date_time'] = self.data[self.turn_count]['candle_date_time_kst']
        return asset_info

    def handle_request(self, request):
        if self.is_initialized is not True:
            self.logger.error('virtual market is not initialized')
            return None

        now = self.data[self.turn_count]['candle_date_time_kst']

        self.turn_count += 1
        next_index = self.turn_count
        if next_index >= len(self.data) - 1:
            return {
                    'request': request,
                    'type': request['type'],
                    'price': 0,
                    'amount': 0,
                    'balance': self.balance,
                    'msg': 'game-over',
                    'date_time': now,
                    'state': 'done'
                    }

        # 수량 혹은 가격이 0이면 그냥 다음 턴으로 넘어간다.
        if request['price'] == 0 or request['amount'] == 0:
            self.logger.warning('turn over')
            return 'error!'

        if request['type'] == 'buy':
            result = self.__handle_buy_request(request, next_index, now)
        elif request['type'] == 'sell':
            result = self.__handle_sell_request(request, next_index, now)
        else:
            self.logger.warning('invalid type request')
            result = 'error!'
        return result


    def __handle_buy_request(self, request, next_index, dt):
        buy_value = request['price'] * request['amount']

        # commission 까지 더한 총 value를 의미한다.
        buy_total_value = buy_value * (1 + self.commission_ratio)
        old_balance = self.balance

        if buy_total_value > self.balance:
            self.logger.info('no money')
            return 'error!'

        try:
            # 요청 거래 가격이 최저 가격보다도 낮다면,
            # 거래가 체결되지 않도록 에러를 반환한다.
            if request['price'] < self.data[next_index]['low_price']:
                self.logger.info('not matched')
                return 'error!'

            name = self.data[next_index]['market']

            if name in self.asset:
                asset = self.asset[name]
                # 저장된 asset amount, value를 업데이트한다.
                new_amount = asset[1] + request['amount']
                new_amount = round(new_amount, 6)
                new_value = (request['amount'] * request['price']) + (asset[0] * asset[1])

                # asset은 가격과 수량을 묶은 페어를 저장한다.
                self.asset[name] = (round(new_value / new_amount), new_amount)
            else:
                self.asset[name] = (request['price'], request['amount'])

            # Q. 왜 round와 - 연산을 같이 하지 않는걸까? 무슨 차이가 있을까?
            # Q. 왜 old_balance는 바로 변하는 데에서 사용하지 않고
            # 이렇게 떨어진 곳에서 사용하는 것일까?
            self.balance -= buy_total_value
            self.balance = round(self.balance)
            self.__print_balance_info('buy', old_balance, self.balance, buy_value)
            return {
                    'request': request,
                    'type': request['type'],
                    'price': request['price'],
                    'amount': request['amount'],
                    'msg': 'success',
                    'balance': self.balance,
                    'state': 'done',
                    'date_time': dt
                    }
        except KeyError as msg:
            self.logger.warning(f"internal error {msg}")
            return 'error!'

    # 근본적으로, index-based 로 거래 요청을 처리하는 게
    # 어떤 문제점이 있는 것인지, 왜 이렇게 구성했는지를
    # 알 수가 없다. 그냥 코드를 완성하고 이해해보라는 
    # 느낌이다.
    def __handle_sell_request(self, request, next_index, dt):
        old_balance = self.balance

        try:
            name = self.data[next_index]['market']

            if name not in self.asset:
                self.logger.info('asset empty')
                return 'error!'

            if request['price'] >= self.data[next_index]['high_price']:
                self.logger.info('not matched')
                return 'error!'

            sell_amount = request['amount']

            if request['amount'] > self.asset[name][1]:
                sell_amount = self.asset[name][1]
                self.logger.warning(f"sell request is bigger than asset {request['amount']} > {sell_amount}") 
                del self.asset[name]
            else:
                new_amount = self.asset[name][1] - sell_amount
                new_amount = round(new_amount, 6)
                self.asset[name] = (self.asset[name][0], new_amount)

            sell_value = sell_amount * request['price']
            self.balance += sell_amount * request['price'] * (1 - self.commission_ratio)
            self.balance = round(self.balance)
            self.__print_balance_info('sell', old_balance, self.balance, sell_value)
            return {
                    'request': request,
                    'type': request['type'],
                    'price': request['price'],
                    'amount': sell_amount,
                    'msg': 'success',
                    'balance': self.balance,
                    'state': 'done',
                    'date_time': dt
                    }
        except KeyError as msg:
            self.logger.error(f"invalid trading data {msg}")
            return 'error!'

    def __print_balance_info(self, trading_type, old, new, total_asset_value):
        self.logger.debug(f"[Balance] from {old}")
        if trading_type == 'buy':
            self.logger.debug(f"[Balance] - {trading_type}_asset_value {total_asset_value}")
        elif trading_type == 'sell':
            self.logger.debug(f"[Balance] + {trading_type}_asset_value {total_asset_value}")
        # Q. 왜 굳이 commission_ratio는 self에서 참조하는 것일까?
        # 어차피 이 함수를 호출하기 전에 self.balance를 업데이트할 것이라면, 
        # 굳이 old, new를 인자로 받을 필요가 있었을까?
        # total value는 두 balance의 차이로 알 수 있지 않았을까?
        self.logger.debug(f"[Balance] - commission {total_asset_value * self.commission_ratio}")
        self.logger.debug(f"[Balance] to {new}")

    def get_account_info(self):
        if self.is_initialized is not True:
            raise UserWarning('Not initialized')
        try:
            return self.market.get_balance()
        except (TypeError, AttributeError) as msg:
            self.logger.error(f"invalid state {msg}")
            raise UserWarning('invalid state') from msg

    def get_balance(self):
        asset_info = { 'balance': self.balance }
        quote = None

        # 키 에러, 인덱스 에러를 별도로 체크하지 않고 try/catch로 처리한다.
        # 꽤 신선하긴 한데, 어떤게 더 괜찮을까?
        try:
            quote = {
                    self.data[self.turn_count]['market']: self.data[self.turn_count]['trade-price']
                    }
            for name, item in self.asset.items():
                self.logger.debug(f"asset item: {name}, item price: {item[0]}, amount: {item[1]}")
        except (KeyError, IndexError) as msg:
            self.logger.error(f"invalid trading data {msg}")
            return None



