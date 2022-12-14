import pandas as pd

df = pd.read_parquet("data/interim/spy_eod.parquet")

# For now, let's focus on *puts* only,
# and also, for a start, let's not overcomplicate this with the Greeks

cols = [
    "[QUOTE_DATE]",
    "[UNDERLYING_LAST]",
    "[EXPIRE_DATE]",
    "[STRIKE]",
    "[P_BID]",  # assume we always operate on bid/ask prices
    "[P_ASK]",
    "[STRIKE_DISTANCE]",  # okay, perhaps these will be convenient
    "[STRIKE_DISTANCE_PCT]",
]

df = df[cols].dropna()
df.to_parquet("data/processed/spy_eod_put.parquet")
