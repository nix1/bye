import pandas as pd
from tqdm import tqdm
from collections import defaultdict

df = pd.read_parquet("data/processed/spy_eod_put.parquet")
df.head()

#%%

# Okay, so backtesting should probably do something like this:
# - [ ] Make an instance of a strategy
#    - [ ] Give it a starting capital
# - [ ] For each day, run the strategy on the data for that day
#    - [ ] The strategy should return a list of trades
#    - [ ] The strategy should also return a list of positions
# - [ ] For each trade, calculate the P&L, and keep track of the capital
# - [ ] Allow the strategy to make trades
#   - [ ] Write/Sell a put
#   - [ ] Buy/Close a put
#   - [ ] Roll a put to a different expiration date

#%%

from src.markets import HistoricalMarket
from src.strategies import SellWeeklyPuts

#%%

market = HistoricalMarket(
    current_date=df["[QUOTE_DATE]"].min(),
    quotes_df=df,
)

# In a loop, advance the market by one day and run the strategy
# On each day/trade, calculate the P&L, and keep track of the capital.
strategies = [
    SellWeeklyPuts(market, capital=0),  # ATM
    SellWeeklyPuts(market, capital=0, ideal_strike=0.9),  # OTM
    SellWeeklyPuts(market, capital=0, ideal_strike=1.1),  # ITM
]

pbar = tqdm(total=len(df["[QUOTE_DATE]"].unique()))

values = defaultdict(list)

while market.can_advance():
    for strategy in strategies:
        strategy.run()
    market.tick()
    pbar.update(1)
    pbar.set_description(f"Current date: {market.current_date}")

    pbar.set_postfix(
        underlying_last=market.underlying_last,
        **{f"{strategy}": strategy.get_current_value() for strategy in strategies},
    )
