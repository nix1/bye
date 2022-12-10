# OptionHodler's Backtesting Yield Estimator

The goal of the OptionHodler's Backtesting Yield Estimator (_OHBYE_) is to provide
a simple Pythonic way to define and test option trading strategies.
This tool aims to allow investors to backtest their option strategies on historical data
to estimate the expected yield of their strategies
_(but see more info on its current state and limitations below)_.

The focus is on testing long-term investment strategies. Write and HODL! 📈💰

## Why?

Because I couldn't find a tool for myself,
and I was disappointed by the state of open-source in this area.
Let's change that!

## Current Status

![flake8 and pytest](https://github.com/nix1/ohbye/actions/workflows/python-app.yml/badge.svg)

🚧 **POC / Exploration** 🚧

OHBYE is currently in its early stages of development,
like a toddler learning to walk and talk. For now, it's just an experiment.
But if you're interested in contributing, I'd love to have your help! 🙌
Check if there are any recent contributions to see if the project is still active.
If not, it may have been abandoned. 🤷‍

## Features
### Implemented Features
OHBYE currently only has limited support for SPY put-writing strategies
based on end-of-day historical data provided by [OptionsDX](https://www.optionsdx.com/).
The author is not affiliated with OptionsDX in any way, I just found
their data to be the most convenient to work with.

### Key Planned Features
One of the key planned features of OHBYE is the ability
to generate semisynthetic option data based on real historical SPY and VIX values.
This will make it much easier to test strategies without the need
for actual historical option data (which might be heavy, expensive or perhaps
lacking or even not available at all).

Long-term, OHBYE might support the generation of purely synthetic data
to detach itself from what happened in the past,
and therefore hopefully better evaluate strategies for the future.

The tool will also provide additional analysis and visualization of backtesting results,
to help users identify the most promising strategies.

## Project Goals
The following goals are in scope for OHBYE:

* 📈 Allow backtesting of options strategies on historical data
  * Support for daily SPY data from OptionsDx
  * Put-write strategies
  * Other and more complex strategies/combinations
  * Keeping track of available capital and enforcing position limits
  * Reporting of results - returns, drawdowns, etc.
  * Charts of results
  * Reporting on metrics - volatility, Sharpe ratio, etc.
  * The impact of commissions and fees
  * Tax implications
  * Margin requirements and interest
* 🔮 Generation of semisynthetic market data based on real SPY and VIX values
  * This is also where tickers other than SPY might be supported, because it will likely
    be easier to generate semisynthetic data for them than to find decent historical data.
* 🔮 Generation of purely synthetic market data to take into account very rare events (black swans)
that might have never occurred in the past.

### Anti-Goals
None of the following is planned to be supported by OHBYE:
* Backtesting on more frequent data. This is not a day-trading tool, it's for long-term strategies.
* Exercise and assignment. Let's just focus on options.  
  **Q:** Isn't this limiting?  
  **A:** Not really. Buy the put back just before assignment,
  and open a [synthetic long position](https://www.optionsplaybook.com/option-strategies/synthetic-long-stock/)
  instead, if that's really what you want.

## Usage
To use OHBYE, you will need to first initialize a virtual
environment using the `requirements.txt` file provided. Like this:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

You also need end-of-day data for the SPY ETF from
[OptionsDX](https://www.optionsdx.com/).
Save it in the `data/raw/spy_eod_raw` directory.
Each year should be represented by a separate subdirectory,
and each month should be saved as a separate text file.

Once you have downloaded and saved the data, run the `1_load.py` script in order to
load and join the data. The joined data is saved as a single parquet file,
`data/interim/spy_eod.parquet`.

Then, run the `2_select.py` script to drop unnecessary columns
and save the processed data at `data/processed/spy_eod.parquet`.

Finally, run the `3_main.py` script to backtest the defined options trading strategies.
The script will print the progress of the backtesting process in the terminal.
In the future, it should generate a summary of the results for each strategy tested.

## How do I define my own strategy?
To define your own strategy, you need to get you hands dirty with code.
Create a new class that inherits from any other strategy defined in `src/strategies.py`.
Note that the crucial part is the `handle_no_open_positions` method, which defines
the logic for opening a new position when there are no open positions.
Everything else is optional, because whatever position you open,
it will eventually expire, and the basic logic for handling expiration
is already defined in the base class.
Then, make sure to add it to the `strategies` list in `3_main.py`.

## Disclaimer
🚨 Use at your own risk 🚨

You are responsible for any losses incurred as a result of using this tool.
See also the [LICENSE](LICENSE).


