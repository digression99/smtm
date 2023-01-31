
from .log_manager import LogManager
from .trader import Trader
from .virtual_market import VirtualMarket

class SimulationTrader(Trader):
    def __init__(self):
        self.logger = LogManager.get_logger(__class__.__name__)
        self.market = VirtualMarket()
        self.is_initialized = False
        self.name = 'Simulation'

    def initialize_simulation(self, end, count, budget):
        self.market.initialize(end, count, budget)
        self.is_initialized = True

    def send_request(self, request_list, callback):
        if self.is_initialized is not True:
            raise UserWarning('Not initialized')

        try:
            result = self.market.handle_request(request_list[0])
            callback(result)
        except (TypeError, AttributeError) as msg:
            self.logger.error(f"invalid state {msg}")
            raise UserWarning('invalid state') from msg

    def get_account_info(self):
        if self.is_initialized is not True:
            raise UserWarning('Not initialized')

        try:
            return self.market.get_balance()
        except (TypeError, AttributeError) as msg:
            self.logger.error(f"invalid state {msg}")
            raise UserWarning('invalid state') from msg

    def cancel_request(self, request_id):
        pass

    def cancel_all_requests(self):
        pass



            
