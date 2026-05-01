# Asset Allocation Portfolio Management

A Python application for implementing various asset allocation strategies including Bold Asset Allocation (BAA), Modified Dual Momentum (MDM), Bond Dynamic Asset Allocation (BDAA), and Hybrid Asset Allocation (HAA).

## ✨ Features

### 🎯 Asset Allocation Strategies
- **Hybrid Asset Allocation (HAA)**: Hybrid approach combining multiple factors
- **Korean All-Weather Strategy**: Seasonal allocation strategy for Korean markets
- **Bold Asset Allocation (BAA)**: Momentum-based strategy with risk management
- **Modified Dual Momentum (MDM)**: Enhanced dual momentum strategy
- **Bond Dynamic Asset Allocation (BDAA)**: Dynamic bond allocation based on performance

### 🚀 Performance & Reliability
- **Intelligent Caching**: Reduces API calls and improves performance
- **Performance Monitoring**: Built-in performance tracking and optimization
- **Comprehensive Error Handling**: Robust error recovery and logging
- **Regression Test Coverage**: Broad pytest suite covering execution flow, CLI, strategies, and services
- **PR Check Workflow**: Pull requests run compile/import sanity checks plus the test suite in CI

### 🛠️ Developer Experience
- **Modular Architecture**: Clean separation of concerns with strategy classes
- **Configuration Management**: Centralized configuration with environment variables
- **CLI Interface**: Command-line tool with multiple output formats
- **Type Hints**: Full type annotation for better code maintainability

### 📊 Output Formats
- **Text**: Human-readable format for console output
- **JSON**: Machine-readable format for API integration
- **CSV**: Spreadsheet-compatible format for analysis

### 🔄 Rebalancing Calculator
- **Input current prices and balances**: Calculate target quantities for rebalancing
- **Automatic portfolio value calculation**: Determine optimal allocation
- **Detailed action reports**: Buy/Sell/Hold recommendations with exact quantities
- **Multiple output formats**: Text, JSON, or CSV for easy analysis

### 🔗 Integrations
- **Telegram Integration**: Automated portfolio updates via Telegram bot
- **FRED API Integration**: Economic data integration (optional)
- **Yahoo Finance**: Real-time financial data

## Installation

### Option 1: Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd AssetAllocation
```

2. Build and run with Docker:
```bash
# Build the optimized multi-stage image
docker build -t asset-allocation .

# Run the container
docker run --rm asset-allocation

# Or use docker-compose
docker-compose up
```

**Docker Image Features:**
- 🐧 **Alpine Linux**: Lightweight base image (~386MB)
- 🏗️ **Multi-stage build**: Optimized for size and security
- 🔒 **Non-root user**: Enhanced security
- 🏥 **Health checks**: Built-in monitoring
- 📦 **Minimal dependencies**: Only runtime packages included

### Option 2: Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AssetAllocation
```

2. Install dependencies (primary local workflow via `uv` + `pyproject.toml`):
```bash
uv sync --group dev
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your API keys
```

## Configuration

Create a `.env` file with the following variables:

```env
# FRED API Key (optional)
FRED_API_KEY=your_fred_api_key_here

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

## Usage

For practical day-to-day run flow (scheduled vs CLI, storage, diff, and history inspection), see [OPERATIONS.md](OPERATIONS.md).


### Execution Paths

- **Scheduled/regular execution (`main.py`)**: production-style run path (currently runs HAA + KAW).
- **Manual analysis (`cli.py` / `asset-cli`)**: user-invoked CLI for ad-hoc strategy runs, output formatting, cache tools, and rebalancing helpers.
- **Shared orchestration (`strategy_runner.py`)**: common strategy dispatch layer used by both entrypoints.
- **CLI strategy execution (`cli_strategy_executor.py`)**: CLI-only strategy runner implementations (BAA/VAA/LAA/BDAA/MDM/HAA/KAW).

### 🖥️ Command Line Interface (manual path)

The application provides a powerful CLI with multiple options:

```bash
# Basic usage - run all strategies
uv run asset-cli

# Run specific strategy
uv run asset-cli --strategy haa
uv run asset-cli --strategy kaw

# Different output formats
uv run asset-cli --output json
uv run asset-cli --output csv
uv run asset-cli --output text

# Save execution results to JSON file
uv run asset-cli --strategy haa --save-json outputs/latest.json

# Compare current run with a previously saved JSON result
uv run asset-cli --strategy haa --compare-json outputs/previous.json

# View scheduled execution history snapshots (latest 10 by default)
uv run asset-cli --history
uv run asset-cli --history 5

# View one saved snapshot in detail
uv run asset-cli --show-history outputs/history/20260102_020202.json

# Verbose logging
uv run asset-cli --verbose

# Cache management
uv run asset-cli --cache-stats
uv run asset-cli --clear-cache

# Performance monitoring
uv run asset-cli --performance

# Rebalancing calculation
uv run asset-cli --rebalance rebalance_example.json
uv run asset-cli --rebalance rebalance_example.json --output json
uv run asset-cli --rebalance rebalance_example.json --output csv

# Custom ticker file
uv run asset-cli --tickers custom_tickers.json
```

### 🐳 Docker Usage

```bash
# Run once
docker run --rm asset-allocation

# Run with environment variables
docker run --rm -e FRED_API_KEY=your_key asset-allocation

# Run with docker-compose (includes environment file)
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f
```

### 💻 Local Usage

```bash
# Scheduled / regular execution path
uv run python main.py

# Manual analysis CLI path
uv run asset-cli

# Run specific strategy
uv run asset-cli --strategy kaw --output json
```

### 🧪 Testing

```bash
# Run all tests
uv run python -m pytest

# Run specific test file
uv run python -m pytest tests/test_strategies.py -v

# Run with coverage
uv run python -m pytest --cov=. --cov-report=html

# Run tests with verbose output
uv run python -m pytest -v --tb=short
```

Pull requests to `master` are validated by `.github/workflows/pr-check.yml`, which installs with `uv`, runs a compile/import sanity check, and executes `pytest`.

## Asset Allocation Strategies

### Bold Asset Allocation (BAA)
- Uses momentum scores to select between aggressive and defensive assets
- Considers 12-month moving averages for risk management

### Modified Dual Momentum (MDM)
- Compares 12-month returns of SPY and IEFA
- Falls back to bond allocation when both are negative

### Bond Dynamic Asset Allocation (BDAA)
- Selects top 3 performing bonds over 6 months
- Allocates to cash if bond performance is negative

### Hybrid Asset Allocation (HAA)
- Uses TIP as a market condition indicator
- Allocates across 4 best-performing assets when TIP is positive

## 🏗️ Project Structure

```
AssetAllocation/
├── main.py                  # Scheduled/regular execution entrypoint
├── cli.py                   # Manual analysis CLI entrypoint (asset-cli)
├── strategy_runner.py       # Shared strategy orchestration layer
├── cli_strategy_executor.py # CLI-specific strategy execution helpers
├── portfolio.py             # Portfolio calculations and allocation helpers
├── config.py                # Configuration and validation
├── strategies/              # Strategy implementations
│   ├── __init__.py
│   ├── base_strategy.py
│   ├── haa_strategy.py
│   ├── korean_all_weather_strategy.py
│   └── ...
├── services/                # Service layer (market/fred/communications)
│   ├── __init__.py
│   ├── data_service.py
│   └── communication_service.py
├── utils/                   # Utility modules (cache, logging, perf, security)
│   ├── __init__.py
│   ├── cache_manager.py
│   └── performance_monitor.py
├── tests/                   # Regression test suite
│   ├── test_main_execution_flow.py
│   ├── test_cli.py
│   ├── test_strategy_runner.py
│   └── ...
├── .github/workflows/
│   └── pr-check.yml         # CI checks for pull requests
├── pyproject.toml           # Project metadata + dependencies + scripts
└── uv.lock                  # Locked dependency set for uv
```

## 📦 Dependencies

Dependencies are managed in `pyproject.toml` and locked in `uv.lock`.

- Install runtime + dev tooling with `uv sync --group dev`
- CLI entrypoints are defined as:
  - `asset-allocation` → `main:main`
  - `asset-cli` → `cli:main`

## 🔧 Configuration

The application uses a centralized configuration system in `config.py`:

- **Strategy Settings**: Configurable parameters for each strategy
- **API Settings**: FRED and Telegram API configuration
- **Cache Settings**: TTL and cache directory configuration
- **Logging Settings**: Log levels and output configuration

## 🚀 Performance Features

- **Intelligent Caching**: Reduces redundant API calls
- **Performance Monitoring**: Tracks execution times and bottlenecks
- **Error Recovery**: Graceful handling of API failures
- **Memory Optimization**: Efficient data structures and cleanup

## 📊 Output Examples

### JSON Output
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "strategies": {
    "HAA": {
      "SPY": 25.0,
      "IWM": 25.0,
      "IEFA": 25.0,
      "TLT": 25.0
    },
    "KAW": {
      "TIGER S&P500": 10.0,
      "KOSEF 200TR": 10.0,
      "KODEX 골드선물(H)": 15.0,
      "TIGER 미국채 10년 선물": 32.5,
      "KOSEF 국고채 10년": 32.5
    }
  }
}
```

### Rebalancing Output Example
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "rebalancing": {
    "SPY": {
      "current_value": 4505.00,
      "target_value": 4750.00,
      "current_quantity": 10,
      "target_quantity": 11,
      "quantity_diff": 1,
      "action": "매수",
      "price": 450.50,
      "target_allocation_pct": 25.0,
      "current_allocation_pct": 20.0
    }
  }
}
```

### CSV Output
```csv
Strategy,Asset,Percentage
HAA,SPY,25.00
HAA,IWM,25.00
HAA,IEFA,25.00
HAA,TLT,25.00
KAW,TIGER S&P500,10.00
KAW,KOSEF 200TR,10.00
```

## 🔄 Rebalancing Usage

The rebalancing calculator helps you determine exact buy/sell quantities to achieve your target asset allocation.

### Step 1: Create a rebalancing input file

Create a JSON file (e.g., `rebalance_example.json`) with the following structure:

```json
{
  "allocation": {
    "SPY": 25.0,
    "IWM": 25.0,
    "IEFA": 25.0,
    "TLT": 25.0
  },
  "current_prices": {
    "SPY": 450.50,
    "IWM": 195.75,
    "IEFA": 68.30,
    "TLT": 95.20
  },
  "current_balances": {
    "SPY": 10,
    "IWM": 25,
    "IEFA": 35,
    "TLT": 50
  }
}
```

**Fields:**
- `allocation`: Target asset allocation percentages
- `current_prices`: Current prices for each asset
- `current_balances`: Current number of shares/units held

### Step 2: Run the rebalancing calculator

```bash
# Text output (default)
uv run asset-cli --rebalance rebalance_example.json

# JSON output
uv run asset-cli --rebalance rebalance_example.json --output json

# CSV output
uv run asset-cli --rebalance rebalance_example.json --output csv
```

### Step 3: Review the results

The calculator will provide:
- Current portfolio value and allocation
- Target allocation for each asset
- Exact number of shares to buy or sell
- Detailed action recommendations

Example text output:
```
리밸런싱 리포트 - 2024-01-15 10:30:00
================================================================================

SPY:
  현재가: $450.50
  현재 수량: 10
  현재 가치: $4505.00
  현재 비중: 20.00%
  목표 비중: 25.00%
  목표 가치: $4750.00
  목표 수량: 11
  조치: 매수 (+1 주)
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **Installation Guide**: Detailed setup instructions
- **Quick Start**: Get up and running quickly
- **API Reference**: Complete API documentation
- **Strategy Guide**: Detailed strategy explanations
- **Configuration**: Configuration options and examples
- **Examples**: Usage examples and best practices
- **Contributing**: How to contribute to the project

### Building Documentation

```bash
# Install documentation dependencies
uv add --dev sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Build documentation
cd docs
uv run sphinx-build -b html source build

# View documentation
open build/index.html
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request

See the [Contributing Guide](docs/source/contributing.rst) for detailed information.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Price provider selection (Yahoo vs Twelve Data)
- Default provider: `PRICE_PROVIDER=yahoo`.
- To use Twelve Data adjusted daily prices: set `PRICE_PROVIDER=twelvedata` and `TWELVEDATA_API_KEY=...`.
- Twelve Data free/basic plans are rate-limited by API credits per minute. You can tune batching with:
  - `TWELVEDATA_MAX_CREDITS_PER_MINUTE` (default: `8`)
  - `TWELVEDATA_REQUEST_SLEEP_SECONDS` (default: `65`)
- Docker example:
  - `docker run --rm -e PRICE_PROVIDER=twelvedata -e TWELVEDATA_API_KEY=... -e TWELVEDATA_MAX_CREDITS_PER_MINUTE=8 -e TWELVEDATA_REQUEST_SLEEP_SECONDS=65 asset-allocation`
- HAA TIP diagnostics (`python cli.py --strategy haa --haa-debug-report`) now includes provider, adjust mode, TIP month-end anchors (T/T-1/T-3/T-6/T-12), 1/3/6/12M returns, TIP 13612U, and final canary decision for source comparison.
