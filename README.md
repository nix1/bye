# SPY Options Strategies Tester

Current state: unusable (POC/exploration)

## Goals

The goal of this project is to provide a simple Pythonic way to define and test options strategies.

The above means several sub-goals:
- [ ] Allow backtesting of options strategies on historical data
- [ ] Synthetically generate historical data based on real SPY values and VIX values
  - This is because real historical data isn't necessarily easy to get, or it's expensive, or incomplete
  - If available, it might be in an inconvenient format or might be impractically large
  - Also, this seems to be a necessary step for generating an entirely synthetic dataset
- [ ] Generate purely synthetic data
  - This is to allow more accurate testing of strategies
  - In particular, this is to take into account very rare events (black swans) that may not have happened in the past


