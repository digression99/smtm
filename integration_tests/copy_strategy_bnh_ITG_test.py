import unittest
from smtm import StrategyBuyAndHold
from unittest.mock import *

class StrategyBuyAndHoldIntegrationTests(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_ITG_get_request_after_update_info_and_result(self):
        strategy = StrategyBuyAndHold()
        self.assertEqual(strategy.get_request(), None)
        strategy.initialize(50000, 5000)

        strategy.update_trading_info(
                {
                    'market': 'KRW-BTC',
                    'date_time': '2020-04-30T14:51:00',
                    'opening_price': 11288000.0,
                    'high_price': 11304000.0,
                    'low_price': 11282000.0,
                    'closing_price': 11304000.0,
                    'acc_price': 587101574.8949,
                    'acc_volume': 51.97606868
                    }
                )

        request = strategy.get_request()
        expected_request = {
                'type': 'buy',
                'price': 11304000.0,
                'amount': 0.0009
                }

        self.assertEqual(request[0]['type'], expected_request['type'])
        self.assertEqual(request[0]['price'], expected_request['price'])
        self.assertEqual(request[0]['amount'], expected_request['amount'])

        strategy.update_result({
            'request': {
                'id': request[0]['id'],
                'type': 'buy',
                'price': 11304000.0,
                'amount': 0.0009,
                'date_time': '2020-04-30T14:51:00'
                },
            'type': 'buy',
            'price': 11304000.0,
            'amount': 0.0009,
            'msg': 'success',
            'balance': 0,
            'state': 'done',
            'date_time': '2020-04-30T14:51:00'
            })

        self.assertEqual(strategy.balance, 39821)

        # 2

        strategy.update_trading_info(
                {
                    'market': 'KRW-BTC',
                    'date_time': '2020-04-30T14:52:00',
                    'opening_price': 11304000.0,
                    'high_price': 21304000.0,
                    'low_price': 11304000.0,
                    'closing_price': 21304000.0,
                    'acc_price': 587101574.8949,
                    'acc_volume': 51.97606868
                    }
                )

        request = strategy.get_request()

        expected_request = {
                'type': 'buy',
                'price': 21304000.0,
                'amount': 0.0005
                }

        self.assertEqual(request[0]['type'], expected_request['type'])
        self.assertEqual(request[0]['price'], expected_request['price'])
        self.assertEqual(request[0]['amount'], expected_request['amount'])

        self.assertEqual(strategy.balance, 39821)

        strategy.update_result({
            'request': {
                'id': request[0]['id'],
                'type': 'buy',
                'price': 11304000.0,
                'amount': 0.0009,
                'date_time': '2020-04-30T14:52:00'
                },
            'type': 'buy',
            'price': 11304000.0,
            'amount': 0.0009,
            'msg': 'success',
            'balance': 0,
            'state': 'requested',
            'date_time': '2020-04-30T14:52:00'
            })

        self.assertEqual(strategy.balance, 39821)
        last_id = request[0]['id']
