# Copilot Instructions for BYE (Backtesting Yield Estimator)

## Repository Overview

**BYE (Backtesting Yield Estimator)** is a Python-based tool for backtesting option trading strategies on historical data, specifically focused on SPY (S&P 500 ETF) put-writing strategies. This is an early-stage POC/exploration project (toddler stage) designed for long-term investment strategies.

**Repository Size**: Small (~112KB in src/)
**Languages**: Python 3
**Target Runtime**: Python 3.10 (CI), Python 3.12+ compatible
**Key Dependencies**: pandas, numpy, scipy, statsmodels, pyarrow, tqdm, pytest, flake8, black, jupyter

## Build and Validation Instructions

### Environment Setup

**IMPORTANT**: Always install setuptools and wheel BEFORE installing other dependencies to avoid numpy build issues:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install setuptools wheel
pip install -r requirements.txt
```

**Note**: The requirements.txt pins old package versions (e.g., numpy==1.23.4) that are incompatible with Python 3.12+. The CI uses Python 3.10. For Python 3.12+, you may need to install dependencies without version pins to get compatible versions.

### Linting

**ALWAYS run flake8 before committing**. The CI runs two flake8 checks:

1. Critical errors (will fail CI):
```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

2. Style warnings (won't fail CI):
```bash
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

**Expected warnings**: You may see `SyntaxWarning: invalid escape sequence '\.'` - this is expected and does not fail the build.

### Testing

**ALWAYS run pytest after making code changes**:

```bash
pytest
```

Or for verbose output:
```bash
pytest -v
```

**Test location**: All tests are in `src/tests/` directory.
**Test files**: `test_markets.py`, `test_options.py`, `test_strategies.py`, `test_wallet.py`
**Expected behavior**: All 55 tests should pass in under 1 second.

### Running the Application

The application requires historical option data from OptionsDX (not included in repo). The workflow is:

1. Place SPY EOD data in `data/spy_eod_raw/` (organized by year subdirectories, monthly .txt files)
2. Run data pipeline:
```bash
python 1_load.py      # Loads and joins data -> data/interim/spy_eod.parquet
python 2_select.py    # Filters columns -> data/processed/spy_eod_put.parquet
python 3_main.py      # Runs backtesting strategies
```

**Note**: The data directory does not exist in the repo and must be created by users.

## Project Layout and Architecture

### Directory Structure

```
./
├── .github/
│   └── workflows/
│       └── python-app.yml          # CI workflow (flake8 + pytest)
├── src/                             # Main package directory
│   ├── __init__.py
│   ├── markets.py                   # HistoricalMarket class (iterator over quotes)
│   ├── options.py                   # Option/Put classes
│   ├── strategies.py                # Strategy base class, SellWeeklyPuts, SellMonthlyPuts
│   ├── wallet.py                    # Wallet and Position classes
│   └── tests/                       # All unit tests
│       ├── test_markets.py
│       ├── test_options.py
│       ├── test_strategies.py
│       └── test_wallet.py
├── 1_load.py                        # Step 1: Load raw data
├── 2_select.py                      # Step 2: Filter data
├── 3_main.py                        # Step 3: Run backtesting
├── requirements.txt                 # Python dependencies (pinned versions)
├── README.md                        # User documentation
├── .gitignore                       # Git ignore file
└── LICENSE                          # MIT-style license
```

### Key Architectural Components

1. **HistoricalMarket** (`src/markets.py`): Iterator that provides daily market data, handles trade execution (sell_to_open, buy, sell, close positions). Groups quotes by date and underlying price.

2. **Option Classes** (`src/options.py`): Abstract Option base class with Put implementation. Handles ITM/OTM logic, expiration checks, intrinsic value calculations.

3. **Strategy Pattern** (`src/strategies.py`): 
   - Abstract `Strategy` base class with `handle_no_open_positions()` method to implement
   - `SellWeeklyPuts`: Sells ~weekly ATM/OTM puts (Mondays to Fridays)
   - `SellMonthlyPuts`: Sells monthly puts (30 DTE)
   - Strategies track capital via Wallet

4. **Wallet/Position** (`src/wallet.py`): Tracks cash and open/closed positions. Position tracks option, quantity (negative for short), cost, and closing details.

### CI/CD Pipeline

**GitHub Actions Workflow**: `.github/workflows/python-app.yml`
- **Trigger**: Push/PR to main branch
- **Python Version**: 3.10
- **Steps**:
  1. Install dependencies (pip install flake8 pytest + requirements.txt)
  2. Lint with flake8 (critical errors will fail build)
  3. Test with pytest (all tests must pass)

**Badge**: Shows build status on README.md

### Code Conventions and Known Issues

**TODOs in codebase**:
- `src/markets.py:90, 110`: Handle cases where option quotes are not found (currently may raise IndexError)

**Code Style**:
- Max line length: 127 characters
- Max complexity: 10
- Use of pandas DataFrames throughout
- Type hints not consistently used

**Testing Approach**:
- Fixtures for sample quote DataFrames
- Focus on core functionality (market iteration, position opening)
- Comprehensive test coverage (55 tests total)

### Key Facts for Making Changes

1. **Data Flow**: Raw data (txt) -> interim (parquet) -> processed (parquet) -> backtesting results
2. **Git Ignore**: Repository has a .gitignore file that excludes venv/, data/, and cache files.
3. **Date Handling**: Uses pandas timestamps throughout. Market quotes grouped by `[QUOTE_DATE]` and `[UNDERLYING_LAST]`.
4. **Column Naming**: OptionsDX data uses bracketed column names like `[STRIKE]`, `[P_BID]`, `[EXPIRE_DATE]`.
5. **Position Convention**: Negative quantity = short position, positive = long position.
6. **Strategy Extension**: To add strategies, inherit from `Strategy` and implement `handle_no_open_positions()`.

### Dependency Notes

- **Critical**: Install setuptools/wheel before other packages
- **numpy**: Version 1.23.4 in requirements.txt only works with Python 3.10, not 3.12+
- **pandas**: Requires pyarrow for parquet support
- **jupyter**: Full stack included for notebook development

### Common Pitfalls

1. **Forgetting virtual environment**: Always activate venv before installing/running
2. **Python version mismatch**: CI uses 3.10; local development may use 3.12+
3. **Missing data directory**: Scripts will fail if data/ directory structure doesn't exist
4. **Flake8 warnings**: The SyntaxWarning about escape sequences is normal, doesn't fail CI
5. **Index errors**: Market methods (buy/sell) can raise IndexError if option not found in quotes

### Validation Steps

Before submitting changes:
1. ✅ Activate virtual environment
2. ✅ Run `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` (must have zero errors)
3. ✅ Run `pytest -v` (all 55 tests must pass)
4. ✅ If modifying core logic, test with sample data if available
5. ✅ Ensure no venv/, data/, or cache files are staged for commit

### Trust These Instructions

These instructions have been validated by:
- Creating a fresh virtual environment
- Installing all dependencies (with setuptools workaround)
- Running both flake8 checks (0 errors, expected warnings)
- Running pytest (55/55 tests passed in <0.5s)
- Exploring all source files and configuration

**Only search for additional information if these instructions are incomplete or found to be incorrect.**
