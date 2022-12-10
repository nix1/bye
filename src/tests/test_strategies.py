import pandas as pd
import pytest
from pytest import fixture

from src.markets import HistoricalMarket
from src.strategies import SellWeeklyPuts


@fixture
def quotes_1d_df():
    return pd.DataFrame(
        {
            "[STRIKE]": [90, 100, 110],
            "[UNDERLYING_LAST]": [99.5, 99.5, 99.5],
            "[P_BID]": [0.1, 1.0, 10.0],
            "[P_ASK]": [0.2, 1.1, 10.1],
            "[QUOTE_DATE]": pd.to_datetime("2020-01-01"),
            "[EXPIRE_DATE]": pd.to_datetime("2020-01-08"),
            "[DTE]": 7,
        }
    )


class TestSellWeeklyPuts:
    def _check_strategy(self, cash, value, market_value, open_positions):
        assert self.strategy.wallet.cash == cash
        assert self.strategy.get_current_value() == pytest.approx(value)
        assert self.strategy.get_current_market_value() == pytest.approx(market_value)
        assert len(self.strategy.get_open_positions()) == open_positions

    def test_opening_new_positions(self, quotes_1d_df):
        market = HistoricalMarket(
            current_date=quotes_1d_df["[QUOTE_DATE]"].min(),
            quotes_df=quotes_1d_df,
        )
        self.strategy = SellWeeklyPuts(market)
        self.strategy.run()

        # Expectation: the strategy should sell 1 ~ATM put for 1.0
        self._check_strategy(
            cash=1.0,
            value=0.5,  # cash + intrinsic value of -0.5
            market_value=-0.1,  # cash (bid value=1.0) - market ask value of 1.1
            open_positions=1,
        )
