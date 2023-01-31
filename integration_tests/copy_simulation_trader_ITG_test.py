import unittest
from smtm import CopySimulationTrader
from unittest.mock import * 

class CopySimulationTraderIntegrationTests(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_ITG_simulation_trader_full(self):
        trader = CopySimulationTrader()
        end_date = "2020-04-30T16:30:00"
        trader.initialize_simulation(end=end_date, count=50, budget=50000)

        request = [
                {
                    'id': 'request_1',
                    'type': 'buy',
                    'price': 11372000.0,
                    'amount': 0.0009,
                    'date_time': '2020-04-30T14:40:00'
                    }
                ]

        expected_result = {
                'request': {
                    'id': 'request_1',
                    'type': 'buy',
                    'price': 11372000.0,
                    'amount': 0.0009,
                    'date_time': '2020-04-30T14:40:00'
                    },
                'type': 'buy',
                'price': 11372000.0,
                'amount': 0.0009,
                'msg': 'success',
                'balance': 39760,
                'state': 'done',
                'date_time': '2020-04-30T15:40:00'
                }

        result = None

        def send_request_callback(callback_result):
            # using nonlocal means it will 
            nonlocal result
            result = callback_result

        trader.send_request(request, send_request_callback)
        self.assertEqual(result, expected_result)

        # request account information.
        expected_account_info = {
                'balance': 43146,
                'asset': { 'KRW-BTC': (11372000.0, 0.0006)},
                'quote': { 'KRW-BTC': 11370000.0 },
                'date_time': '2020-04-30T15:42:00'
                }

        account_info = trader.get_account_info()
        self.assertEqual(account_info, expected_account_info)
