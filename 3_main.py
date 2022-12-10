import itertools
from collections import defaultdict

import pandas as pd
from tqdm import tqdm

df = pd.read_parquet("data/processed/spy_eod_put.parquet")
df.head()

#%%

# Okay, so backtesting should probably do something like this:
# - [x] Make an instance of a strategy
#    - [ ] Give it a starting capital
# - [x] For each day, run the strategy on the data for that day
#    - [ ] The strategy should return a list of trades
#    - [x] The strategy should also return a list of positions
# - [ ] For each trade, calculate the P&L, and keep track of the capital
# - [x] Allow the strategy to make trades
#   - [x] Write/Sell a put
#   - [x] Buy/Close a put
#   - [x] Roll a put to a different expiration date

#%%

from src.markets import HistoricalMarket
from src.strategies import SellMonthlyPuts, SellWeeklyPuts

#%%

market = HistoricalMarket(
    current_date=df["[QUOTE_DATE]"].min(),
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

pbar = tqdm(total=len(df["[QUOTE_DATE]"].unique()))

values = defaultdict(list)

while market.can_advance():
    for strategy in strategies:
        strategy.run()
    market.tick()
    pbar.update(1)
    pbar.set_description(market.current_date.strftime("%Y-%m-%d"))

    pbar.set_postfix(
        last=market.underlying_last,
        **{
            f"{strategy}": strategy.get_current_market_value()
            for strategy in strategies
        },
    )
