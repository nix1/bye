import pandas as pd
from pandas.testing import assert_frame_equal
from pytest import fixture

from src.markets import HistoricalMarket
from src.options import Put
from src.wallet import Position


@fixture
def quotes_1d_df():
    return pd.DataFrame(
        {
            "[STRIKE]": [90, 100, 110],
            "[UNDERLYING_LAST]": [99, 99, 99],
            "[P_BID]": [1, 2, 3],
            "[P_ASK]": [1.1, 2.1, 3.1],
            "[QUOTE_DATE]": pd.to_datetime("2020-01-01"),
            "[EXPIRE_DATE]": pd.to_datetime("2020-01-08"),
            "[DTE]": [7, 7, 7],
        }
    )


@fixture
def quotes_8w_df(quotes_1d_df):
    df = pd.DataFrame()
    for i in range(8):
        quotes_copy = quotes_1d_df.copy()
        quotes_copy["[QUOTE_DATE]"] = pd.to_datetime("2020-01-01") + pd.Timedelta(
            days=i * 7
        )
        quotes_copy["[EXPIRE_DATE]"] = pd.to_datetime("2020-01-01") + pd.Timedelta(
            days=i * 7 + 7
        )
        quotes_copy["[UNDERLYING_LAST]"] = 99 + i
        df = pd.concat([df, quotes_copy])
    return df


class TestHistoricalMarket:
    def test_instance(self, quotes_1d_df):
        market = HistoricalMarket(
            quotes_df=quotes_1d_df,
        )
        assert market.current_date is None
        assert market.current_quotes is None
        assert market.underlying_last is None

    def test_first_date(self, quotes_1d_df):
        market = HistoricalMarket(
            quotes_df=quotes_1d_df,
        )
        date, price, quotes = next(market)
        assert date == quotes_1d_df["[QUOTE_DATE]"].iloc[0]
        assert market.current_date == quotes_1d_df["[QUOTE_DATE]"].iloc[0]
        assert_frame_equal(
            market.current_quotes,
            quotes_1d_df.drop(columns=["[QUOTE_DATE]", "[UNDERLYING_LAST]"]),
        )

    def test_iteration(self, quotes_8w_df):
        market = HistoricalMarket(quotes_df=quotes_8w_df)
        assert len(market) == 8

        i = 0
        for date, price, quotes in market:
            assert date == market.current_date
            assert date == pd.to_datetime("2020-01-01") + pd.Timedelta(days=i * 7)
            assert price == market.underlying_last
            assert price == 99 + i
            i += 1

        assert i == 8

    def test_sell_to_open_finds_closest_strike(self, quotes_1d_df):
        """Test sell_to_open finds the option with closest strike"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)  # Advance to first date

        # Request strike of 101 (closest is 100)
        position = market.sell_to_open(ideal_strike=101, ideal_dte=7)
        assert position.option.strike == 100
        assert position.quantity == -1
        assert position.cost == 2  # P_BID for strike 100

    def test_sell_to_open_finds_closest_dte(self, quotes_1d_df):
        """Test sell_to_open finds the option with closest DTE"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)

        # All have DTE=7, so should still work
        position = market.sell_to_open(ideal_strike=100, ideal_dte=5)
        assert position.option.strike == 100
        assert position.option.expiration == pd.to_datetime("2020-01-08")

    def test_sell_to_open_creates_short_position(self, quotes_1d_df):
        """Test sell_to_open creates a short position"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)

        position = market.sell_to_open(ideal_strike=100, ideal_dte=7)
        assert position.quantity == -1  # Short position
        assert position.cost > 0  # Premium received

    def test_buy_returns_ask_price(self, quotes_1d_df):
        """Test buy method returns the ask price"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)

        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        cost = market.buy(put)
        assert cost == 2.1  # P_ASK for strike 100

    def test_sell_returns_bid_price(self, quotes_1d_df):
        """Test sell method returns the bid price"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)

        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        price = market.sell(put)
        assert price == 2  # P_BID for strike 100

    def test_close_long_position_sells_at_bid(self, quotes_1d_df):
        """Test closing a long position sells at bid price"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)

        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        position = Position(option=put, quantity=1, cost=2.1)
        close_value = market.close(position)
        assert close_value == 2  # quantity * bid = 1 * 2

    def test_close_short_position_buys_at_ask(self, quotes_1d_df):
        """Test closing a short position buys at ask price"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)

        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        position = Position(option=put, quantity=-1, cost=2.0)
        close_value = market.close(position)
        assert close_value == -2.1  # quantity * ask = -1 * 2.1

    def test_close_expires_worthless_otm(self, quotes_1d_df):
        """Test that OTM option expiring today has zero close value"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)
        market.current_date = pd.to_datetime("2020-01-08")  # Expiration date

        # OTM put (strike 90, underlying 99)
        put = Put(strike=90, expiration=pd.to_datetime("2020-01-08"))
        position = Position(option=put, quantity=-1, cost=0.1)
        close_value = market.close(position)
        assert close_value == 0  # Expires worthless

    def test_close_dry_run_doesnt_close_position(self, quotes_1d_df):
        """Test that dry_run=True doesn't actually close the position"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)

        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        position = Position(option=put, quantity=-1, cost=2.0)

        # Dry run should return value but not close
        close_value = market.close(position, dry_run=True)
        assert close_value == -2.1
        assert position.close_value is None  # Not actually closed
        assert position.closed_at is None

    def test_close_not_dry_run_closes_position(self, quotes_1d_df):
        """Test that dry_run=False actually closes the position"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)

        put = Put(strike=100, expiration=pd.to_datetime("2020-01-08"))
        position = Position(option=put, quantity=-1, cost=2.0)

        close_value = market.close(position, dry_run=False)
        assert close_value == -2.1
        assert position.close_value == -2.1  # Actually closed
        assert position.closed_at == market.current_date

    def test_get_quotes_returns_current_quotes(self, quotes_1d_df):
        """Test get_quotes returns current market quotes"""
        market = HistoricalMarket(quotes_df=quotes_1d_df)
        next(market)

        quotes = market.get_quotes()
        assert quotes is not None
        assert len(quotes) == 3  # Three strikes
