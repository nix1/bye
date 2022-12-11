import itertools

import pandas as pd
from tqdm import tqdm

from src.markets import HistoricalMarket
from src.strategies import SellMonthlyPuts, SellWeeklyPuts

df = pd.read_parquet("data/processed/spy_eod_put.parquet")


market = HistoricalMarket(
    quotes_df=df,
)

# In a loop, advance the market by one day and run the strategy
# On each day/trade, calculate the P&L, and keep track of the capital.
strategies = []

for StrategyClass, ideal_strike, hold_the_strike in itertools.product(
    [SellWeeklyPuts, SellMonthlyPuts], [0.9, 1.0, 1.1], [False, True]
):
    strategies.append(
        StrategyClass(
            market,
            capital=0,
            ideal_strike=ideal_strike,
            hold_the_strike=hold_the_strike,
        )
    )

for date, price, quotes in (pbar := tqdm(market)):
    for strategy in strategies:
        strategy.run()

    pbar.set_description(market.current_date.strftime("%Y-%m-%d"))

    pbar.set_postfix(
        last=market.underlying_last,
        **{
            f"{strategy}": strategy.get_current_market_value()
            for strategy in strategies
        },
    )
