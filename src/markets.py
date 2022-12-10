from abc import abstractmethod
from datetime import timedelta

from src.options import Put
from src.wallet import Position


class HistoricalMarket:
    """
    Holds the current state of the market.
    Knows the current date and the current quotes.
    Responsible for executing trades.
    """

    def __init__(self, current_date, quotes_df):
        self.quotes_df = quotes_df
        self.current_date = current_date
        self.current_quotes = self.get_quotes(current_date)
        self.underlying_last = self._get_underlying_last()

    def sell_to_open(self, ideal_strike, ideal_dte):
        """Write a put with the strike and dte closest to the ideal ones.
        Sell the put at the current bid price.

        Note that the caller is responsible for adding the position to the wallet,
        and for keeping track of available cash.

        :returns: A new Position object
        """
        # Find the closest option in the quotes dataframe
        quotes_df = self.get_quotes().copy()
        quotes_df["_strike_distance"] = (quotes_df["[STRIKE]"] - ideal_strike).abs()
        quotes_df["_dte_distance"] = (quotes_df["[DTE]"] - ideal_dte).abs()

        # Order by strike distance, then by dte distance
        quotes_df.sort_values(
            by=["_strike_distance", "_dte_distance"],
            inplace=True,
        )

        # Get the first row
        row = quotes_df.iloc[0]

        # Create a put object
        put = Put(
            strike=row["[STRIKE]"],
            expiration=row["[EXPIRE_DATE]"],
        )

        # Create a position object
        position = Position(
            option=put,
            quantity=-1,
            cost=row["[P_BID]"],
        )

        # Return the position
        return position

    def sell(self, option):
        """Sell an option at the current bid price."""
        quotes = self.get_quotes()

        # Find the row with the matching option
        # TODO: what if it's not found?
        return quotes.loc[
            (quotes["[EXPIRE_DATE]"] == option.expiration)
            & (quotes["[STRIKE]"] == option.strike),
            "[P_BID]",
        ].values[0]

    def buy(self, option):
        """Buy an option at the current ask price.

        Note that this doesn't open or close any positions.
        The caller is responsible for adding the position to the wallet,
        and for keeping track of available cash.

        :returns: The cost of the option
        """
        quotes = self.get_quotes()

        # Find the row with the matching option
        # TODO: what if it's not found?
        return quotes.loc[
            (quotes["[EXPIRE_DATE]"] == option.expiration)
            & (quotes["[STRIKE]"] == option.strike),
            "[P_ASK]",
        ].values[0]

    def close(self, position: Position, dry_run=False):
        """Close a position.

        :returns: The credit/debit from closing the position (NOT the profit/loss)
        """
        if position.option.is_expiring(
            self.current_date
        ) and not position.option.is_itm(self.underlying_last):
            # Expires worthless, no need to buy/sell
            close_value = 0
        elif position.quantity > 0:
            close_value = self.sell(position.option) * position.quantity
            assert (
                close_value >= 0
            ), "Close value should be positive when closing a short position"
        else:
            close_value = self.buy(position.option) * position.quantity
            assert (
                close_value <= 0
            ), "Close value should be negative when closing a short position"

        if not dry_run:
            # Actually close it (vs. just evaluating its value)
            position.close(self.current_date, close_value)
        return close_value

    def get_quotes(self, date=None):
        """Get the quotes for a given date.


        :returns: A Pandas dataframe of quotes
            - [QUOTE_DATE] - The date of the quote
            - [UNDERLYING_LAST] - The last price of the underlying
            - [EXPIRE_DATE] - The expiration date of the option
            - [DTE] - The days to expiration
            - [STRIKE] - The strike price of the option
            - [P_BID] - The bid price of the put
            - [P_ASK] - The ask price of the put
            - [STRIKE_DISTANCE] - The distance of the strike from the underlying
            - [STRIKE_DISTANCE_PCT] - The distance of the strike from the underlying, as a percentage
        """
        if date is None:
            if self.current_date is None:
                raise Exception("No current date set")
            date = self.current_date
        return self.quotes_df[self.quotes_df["[QUOTE_DATE]"] == date]

    def _get_underlying_last(self):
        return self.get_quotes()["[UNDERLYING_LAST]"].iloc[0]

    def can_advance(self):
        """Check if the market can advance to the next day."""
        return self.current_date < self.quotes_df["[QUOTE_DATE]"].max()

    def tick(self):
        """Advance the market to the next working day."""
        if not self.can_advance():
            raise Exception("Cannot advance the market")
        # Find the next working day
        future_df = self.quotes_df[self.quotes_df["[QUOTE_DATE]"] > self.current_date]
        self.current_date = future_df["[QUOTE_DATE]"].min()
        # Get the underlying price
        self.underlying_last = self._get_underlying_last()
