import pandas as pd
from pandas.testing import assert_frame_equal
from pytest import fixture

from src.markets import HistoricalMarket


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
        }
    )


@fixture
def quotes_8w_df(quotes_1d_df):
    df = pd.DataFrame()
    for i in range(8):
        quotes_1d_df["[QUOTE_DATE]"] = pd.to_datetime("2020-01-01") + pd.Timedelta(
            days=i * 7
        )
        quotes_1d_df["[EXPIRE_DATE]"] = pd.to_datetime("2020-01-01") + pd.Timedelta(
            days=i * 7 + 7
        )
        quotes_1d_df["[UNDERLYING_LAST]"] = 99 + i
        df = pd.concat([df, quotes_1d_df])
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
        print("Quotes:")
        print(quotes)
        print("Current quotes:")
        print(market.current_quotes)
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
