import os

import pandas as pd
from tqdm import tqdm

directory = "data/spy_eod_raw"  # EOD data from OptionsDx

# Assume these are already unpacked into directories,
# and each directory contains multiple csv files (one per month),
# except the extension is .txt

df = []

# Walk through the directory and read in all the files
for root, dirs, files in (pbar := tqdm(list(os.walk(directory)))):
    pbar.set_description(root.split("/")[-1])
    for file in files:
        pbar.set_postfix_str(file)
        if file.endswith(".txt"):
            part = pd.read_csv(
                os.path.join(root, file),
                low_memory=False,
                parse_dates=[
                    " [QUOTE_READTIME]",
                    " [QUOTE_DATE]",
                    " [EXPIRE_DATE]",
                ],
            )
            # Remove spaces from column names
            part.columns = part.columns.str.strip()

            # Drop the columns we don't need
            part.drop(
                columns=[
                    "[C_SIZE]",
                    "[P_SIZE]",
                ],
                inplace=True,
            )

            # Convert all 'object' columns to 'float'
            for col in part.columns:
                if part[col].dtype == "object":
                    # Note that some values can't be converted,
                    # that's why we use 'coerce' and not 'raise'
                    part[col] = pd.to_numeric(part[col], errors="coerce")

            df.append(part)

# Concatenate all the dataframes into one
df = pd.concat(df, ignore_index=True)

# Show what we have
memory_usage_mb = df.memory_usage(deep=True).sum() / 1024**2
print(f"Loaded {df.shape[0]:,} rows, {df.shape[1]} columns, {memory_usage_mb:.2f} MB")

# Save the dataframe as a parquet file
df.to_parquet("data/interim/spy_eod.parquet")
memory_usage_mb = os.path.getsize("data/interim/spy_eod.parquet") / 1024**2
print(
    f"Saved {df.shape[0]:,} rows to data/interim/spy_eod.parquet,  {memory_usage_mb:.2f} MB"
)
