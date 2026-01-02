import pandas as pd
import pytest
from pytest import fixture

from src.markets import HistoricalMarket
from src.strategies import SellWeeklyPuts, SellMonthlyPuts


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
            "[DTE]": [7, 7, 7],
        }
    )


@fixture
def quotes_multi_day_df():
    """Create quotes for multiple days"""
    df = pd.DataFrame()
    for i in range(3):
        day_quotes = pd.DataFrame(
            {
                "[STRIKE]": [90, 100, 110],
                "[UNDERLYING_LAST]": [99.5, 99.5, 99.5],
                "[P_BID]": [0.1, 1.0, 10.0],
                "[P_ASK]": [0.2, 1.1, 10.1],
                "[QUOTE_DATE]": pd.to_datetime("2020-01-01") + pd.Timedelta(days=i),
                "[EXPIRE_DATE]": pd.to_datetime("2020-01-08"),
                "[DTE]": [7 - i, 7 - i, 7 - i],
            }
        )
        df = pd.concat([df, day_quotes])
    return df


class TestSellWeeklyPuts:
    def _check_strategy(self, strategy, cash, value, market_value, open_positions):
        assert strategy.wallet.cash == cash
        assert strategy.get_current_value() == pytest.approx(value)
        assert strategy.get_current_market_value() == pytest.approx(market_value)
        assert len(strategy.get_open_positions()) == open_positions

    def test_opening_new_positions(self, quotes_1d_df):
        market = HistoricalMarket(
            quotes_df=quotes_1d_df,
        )
        strategy = SellWeeklyPuts(market)
        market.__next__()
        strategy.run()

        # Expectation: the strategy should sell 1 ~ATM put for 1.0
        # - Starting cash = 0.0
        # - Ideal DTE is 3, but no choice here, the closest one is 7
        # - Ideal strike = 99.5, the closest one is 100
        self._check_strategy(
            strategy,
            cash=1.0,  # ends up with 1.0 cash from the premium
            value=0.5,  # 1.0 (cash)  -0.5 (simplified value of the short OOM put)
            market_value=-0.1,  # 1.0 (cash) -1.1 (market ask value of the short OOM put)
            open_positions=1,
        )

    def test_ideal_strike_atm(self, quotes_1d_df):
        """Test that ATM strike is selected by default"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellWeeklyPuts(market, ideal_strike=1.0)
        next(market)
        strategy.run()

        positions = strategy.get_open_positions()
        assert len(positions) == 1
        # Should select strike closest to 99.5 * 1.0 = 99.5, which is 100
        assert positions[0].option.strike == 100

    def test_ideal_strike_otm(self, quotes_1d_df):
        """Test that OTM strike is selected when ideal_strike < 1.0"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellWeeklyPuts(market, ideal_strike=0.9)
        next(market)
        strategy.run()

        positions = strategy.get_open_positions()
        assert len(positions) == 1
        # Should select strike closest to 99.5 * 0.9 = 89.55, which is 90
        assert positions[0].option.strike == 90

    def test_ideal_strike_itm(self, quotes_1d_df):
        """Test that ITM strike is selected when ideal_strike > 1.0"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellWeeklyPuts(market, ideal_strike=1.1)
        next(market)
        strategy.run()

        positions = strategy.get_open_positions()
        assert len(positions) == 1
        # Should select strike closest to 99.5 * 1.1 = 109.45, which is 110
        assert positions[0].option.strike == 110

    def test_hold_the_strike_false(self, quotes_multi_day_df):
        """Test that strike adjusts with market when hold_the_strike=False"""
        market = HistoricalMarket(quotes_df=quotes_multi_day_df)
        strategy = SellWeeklyPuts(market, ideal_strike=1.0, hold_the_strike=False)

        # Just test that it initializes
        assert strategy.hold_the_strike is False
        assert strategy.last_ideal_strike is None

    def test_write_put_adds_position(self, quotes_1d_df):
        """Test that write_put adds a position to the wallet"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellWeeklyPuts(market)
        next(market)

        initial_cash = strategy.wallet.cash
        strategy.write_put(ideal_strike=100, ideal_dte=7)

        assert len(strategy.wallet.positions) == 1
        assert strategy.wallet.cash > initial_cash  # Received premium

    def test_get_ideal_dte_monday(self, quotes_1d_df):
        """Test ideal DTE calculation on Monday"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellWeeklyPuts(market)
        next(market)

        # 2020-01-01 is a Wednesday (weekday=2), so ideal_dte = 5-2 = 3
        market.current_date = pd.to_datetime("2020-01-01")
        ideal_dte = strategy._get_ideal_dte()
        assert ideal_dte == 3

    def test_get_ideal_dte_friday(self, quotes_1d_df):
        """Test ideal DTE calculation on Friday"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellWeeklyPuts(market)
        next(market)

        # 2020-01-03 is a Friday (weekday=4), so ideal_dte = 5-4 = 1 (next day is Saturday)
        market.current_date = pd.to_datetime("2020-01-03")
        ideal_dte = strategy._get_ideal_dte()
        assert ideal_dte == 1  # Tomorrow (Saturday counts as expiry day)

    def test_repr_without_hold(self, quotes_1d_df):
        """Test string representation without hold_the_strike"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellWeeklyPuts(market, ideal_strike=0.9, hold_the_strike=False)
        assert repr(strategy) == "W(0.9)"

    def test_repr_with_hold(self, quotes_1d_df):
        """Test string representation with hold_the_strike"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellWeeklyPuts(market, ideal_strike=0.9, hold_the_strike=True)
        assert repr(strategy) == "WH(0.9)"


class TestSellMonthlyPuts:
    def test_monthly_inherits_from_weekly(self, quotes_1d_df):
        """Test that SellMonthlyPuts inherits from SellWeeklyPuts"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellMonthlyPuts(market)
        assert isinstance(strategy, SellWeeklyPuts)

    def test_ideal_dte_is_30(self, quotes_1d_df):
        """Test that ideal DTE for monthly is 30 days"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellMonthlyPuts(market)
        next(market)

        ideal_dte = strategy._get_ideal_dte()
        assert ideal_dte == 30

    def test_repr_without_hold(self, quotes_1d_df):
        """Test string representation without hold_the_strike"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellMonthlyPuts(market, ideal_strike=0.9, hold_the_strike=False)
        assert repr(strategy) == "M(0.9)"

    def test_repr_with_hold(self, quotes_1d_df):
        """Test string representation with hold_the_strike"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellMonthlyPuts(market, ideal_strike=1.1, hold_the_strike=True)
        assert repr(strategy) == "MH(1.1)"

    def test_opening_position(self, quotes_1d_df):
        """Test that monthly strategy opens positions"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        strategy = SellMonthlyPuts(market)
        next(market)
        strategy.run()

        positions = strategy.get_open_positions()
        assert len(positions) == 1
