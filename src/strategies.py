from abc import abstractmethod

from src.options import Put
from src.wallet import Wallet


class Strategy:
    def __init__(self, market, capital=0):
        self.market = market
        self.wallet = Wallet(capital)

    def write_put(self, ideal_strike, ideal_dte):
        assert ideal_strike is not None
        assert ideal_strike > 0
        position = self.market.sell_to_open(ideal_strike, ideal_dte)
        self.wallet.add_position(position, update_cash=True)

        # Return the position for convenience
        return position

    def handle_expiring_positions(self, positions):
        # By default, buy them back and close the position
        for position in positions:
            profit = self.market.close(position)
            self.wallet.cash += profit

    def handle_open_positions(self, positions):
        pass

    @abstractmethod
    def handle_no_open_positions(self):
        pass

    def run(self):
        """
        Run the strategy on the market data

        The default implementation for convenience
        runs separately each of the common situations which might occur.
        """
        # First, the expiring ones MUST be handled
        if positions := self.wallet.get_expiring_positions(self.market.current_date):
            self.handle_expiring_positions(positions)

        # Then, handle the open ones (by default, do nothing)
        if positions := self.wallet.get_open_positions(self.market.current_date):
            # Note that in practice they might be rolled here,
            # but for simplicity you can just close them,
            # and then open new ones
            self.handle_open_positions(positions)

        # Then, if there are no open positions, might open new ones
        if not self.wallet.get_open_positions(self.market.current_date):
            self.handle_no_open_positions()

    def get_current_value(self):
        value = self.wallet.cash  # get the cash
        assert value is not None
        for position in self.wallet.get_open_positions(self.market.current_date):
            # TODO: use market data instead to include the extrinsic value as well
            value += position.option.intrinsic_value(self.market.underlying_last)
        return value


class SellWeeklyATMPuts(Strategy):
    """
    Sell ~weekly ATM puts, every ~Monday to expire on Friday.
    Don't allow assignment. If the put is ITM at expiration (Friday),
    roll it to the next expiration, by buying it back
    and selling a new - now ATM - put.
    """

    def _get_ideal_dte(self):
        # How many days until Friday?
        ideal_dte = 5 - self.market.current_date.weekday()

        # If it's Friday, should sell a put for next Friday
        if ideal_dte == 0:
            ideal_dte = 7

        return ideal_dte

    def handle_expiring_positions(self, positions):
        assert (
            len(positions) == 1
        ), "This strategy only supports one open position at a time"
        for position in positions:
            # If it's ITM, roll it to the next expiration
            if position.option.is_itm(self.market.underlying_last):
                # Buy it back and close the position
                self.market.close(position)
            # else, it's OTM and assume the expiration is handled automatically elsewhere

    def handle_no_open_positions(self):
        assert (
            len(self.wallet.get_open_positions(self.market.current_date)) == 0
        ), "This method should only be called if there are no open positions"
        # Write a new ATM put
        self.write_put(
            ideal_strike=self.market.underlying_last, ideal_dte=self._get_ideal_dte()
        )
