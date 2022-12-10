import pandas as pd
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
            current_date=quotes_1d_df["[QUOTE_DATE]"].min(),
            quotes_df=quotes_1d_df,
        )
        assert market.current_date == quotes_1d_df["[QUOTE_DATE]"].min()
        assert market.quotes_df.equals(quotes_1d_df)
        assert market.underlying_last == 99
        assert not market.can_advance()

    def test_tick(self, quotes_8w_df):
        market = HistoricalMarket(
            current_date=quotes_8w_df["[QUOTE_DATE]"].min(),
            quotes_df=quotes_8w_df,
        )
        assert market.can_advance()
        assert market.underlying_last == 99
        for i in range(7):
            assert market.current_date == pd.to_datetime("2020-01-01") + pd.Timedelta(
                days=i * 7
            )
            market.tick()
        assert market.underlying_last == 106
        assert not market.can_advance()
