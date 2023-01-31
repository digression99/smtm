import copy
import requests

from .date_converter import DateConverter
from .data_provider import DataProvider
from .log_manager import LogManager

class CopySimulationDataProvider(DataProvider):
    URL = 'https://api.upbit.com/v1/candles/minutes/1'
    QUERY_STRING = { 'market' : 'KRW-BTC' }

    def __init__(self):
        self.logger = LogManager.get_logger(__class__.__name__)
        self.is_initialized = False
        self.data = []
        self.index = 0

    def initialize_simulation(self, end=None, count=100):
        self.index = 0
        query_string = copy.deepcopy(self.QUERY_STRING)

        try:
            if end is not None:
                query_string['to'] = DateConverter.from_kst_to_utc_str(end) + 'Z'
            query_string['count'] = count


            self.data = response.json()
            self.data.reverse() # is in-place function?
            self.is_initialized = True
            self.logger.info(f"data is updated from server # end : {end}, count: {count}")
        except ValueError as error:
            self.logger.error('Invalid data from server')
            raise UserWarning('Fail get data from server') from error
        except requests.exceptions.HTTPError as error:
            self.logger.error(error)
            raise UserWarning('Fail get data from server') from error
        except requests.exceptions.RequestException as error:
            self.logger.error(error)
            raise UserWarning('Fail get data from server') from error

    def get_info(self):
        now = self.index
        if now >= len(self.data):
            return None

        self.index = now + 1
        self.logger.info(f'[DATA] @ {self.data[now]["candle_date_time_kst"]}')
        return self.__create_candle_info(self.data[now])

    def __create_candle_info(self, data):
        try:
            return {
                    'market': data['market'],
                    'date_time': data['candle_date_time_kst'],
                    'opening_price': data['opening_price'],
                    'high_price': data['high_price'],
                    'low_price': data['low_price'],
                    'closing_price': data['trade_price'],
                    'acc_price': data['candle_acc_trade_price'],
                    'acc_volume': data['candle_acc_trade_volume']
                    }
        except KeyError:
            self.logger.warning('invalid data for candle info')
            return None
    def initialize_from_server(self, end=None, count=100):
        self.initialize_simulation(end, count)



