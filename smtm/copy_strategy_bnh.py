import copy
import time
from datetime import datetime
from .strategy import Strategy
from .log_manager import LogManager

class StrategyBuyAndHold(Strategy):
    """
    is_initialized - 최초 잔고는 초기화할 때만 갱신.
    data: 거래 데이터 리스트. OHLCV
    result: 거래 요청 결과 리스트
    request: 마지막 거래 요청
    budget: 시작 잔고
    balance: 현재 잔고
    min_price: 최소 주문 금액
    """

    ISO_DATEFORMAT = '%Y-%m-%dT%H:%M:%S'
    COMMISSION_RATIO = 0.0005

    def __init__(self):
        self.is_initialized = False
        self.is_simulation = False
        self.data = []
        self.budget = 0
        self.balance = 0.0
        self.min_price = 0
        self.result = []
        self.request = None
        self.logger = LogManager.get_logger(__class__.__name__)
        self.name = 'BnH'
        self.waiting_requests = {} # waiting_requests는 dict이다.

    def initialize(self, budget, min_price=5000):
        if self.is_initialized:
            return
        self.is_initialized = True
        self.budget = budget
        self.balance = budget
        self.min_price = min_price

    def update_trading_info(self, info):
        if self.is_initialized is not True:
            return
        self.data.append(copy.deepcopy(info))

    def get_request(self):
        if self.is_initialized is not True:
            return

        try:
            if len(self.data) == 0 or self.data[-1] is None:
                raise UserWarning('data is empty')

            last_closing_price = self.data[-1]['closing_price']
            now = datetime.now().strftime(self.ISO_DATEFORMAT)

            # Why are you checking if this is simulation?
            if self.is_simulation:
                now = self.data[-1]['date_time']

            # Can I change this to inline if/else?
            target_budget = self.budget / 5
            if target_budget > self.balance:
                target_budget = self.balance

            amount = round(target_budget / last_closing_price, 4)
            trading_request = {
                    'id': str(round(time.time(), 3)),
                    'type': 'buy',
                    'price': last_closing_price,
                    'amount': amount,
                    'date_time': now
                    }

            # total requesting value.
            total_value = round(float(last_closing_price) * amount)

            # 최소 주문보다 전체 주문 금액이 낮다면 에러.
            if self.min_price > total_value or total_value > self.balance:
                raise UserWarning('total_value or balance is too small.')

            # logs.
            self.logger.info(f"[REQ] id: {trading_request['id']}")
            self.logger.info(f"price: {last_closing_price}, amount: {amount}")
            self.logger.info(f"type: buy, total value: {total_value}")

            final_requests = []
            for request_id in self.waiting_requests:
                self.logger.info(f"cancel request added! {request_id}")
                final_requests.append({
                    'id': request_id,
                    'type': 'cancel',
                    'price': 0,
                    'amount': 0,
                    'date_time': now
                    })
            final_requests.append(trading_request)
            return final_requests
        except (ValueError, KeyError) as msg:
            self.logger.error(f"invalid data {msg}")
        except IndexError:
            self.logger.error("empty data")
        except AttributeError as msg:
            self.logger.error(msg)
        except UserWarning as msg:
            self.logger.info(msg)
            if self.is_simulation:
                return [{
                    'id': str(round(time.time(), 3)),
                    'type': 'buy',
                    'price': 0,
                    'amount': 0,
                    'date_time': now
                    }]
            return None
    def update_result(self, result):
        """
        request - 거래 요청 정보
        """
        if self.is_initialized is not True:
            return
        try:
            request = result['request']
            id = request['id']
            if result['state'] == 'requested':
                # id가 리스트의 인덱스로 참조된다?
                self.waiting_requests[id] = result
                return
            if result['state'] == 'done' and id in self.waiting_requests:
                del self.waiting_requests[id]

            total = float(result['price']) * float(result['amount'])
            fee = total * self.COMMISSION_RATIO

            # 이게 무슨 의미일까? 구매시에는 total, fee가 빠지는 건 알겠는데
            # 왜 다른 경우에 balance가 더해지는 걸까?
            if result['type'] == 'buy':
                self.balance -= round(total + fee)
            else:
                self.balance += round(total - fee)

            # logs
            self.logger.info(f"[RESULT] id: {result['request']['id']}")
            self.logger.info(f"type: {result['type']}, msg: {result['msg']}")
            self.logger.info(f"price: {result['price']}")

        # tuple 로 묶으면 한꺼번에 같은 타입을 처리할 수 있다?
        except (AttributeError, TypeError) as msg:
            self.logger.error(msg)







