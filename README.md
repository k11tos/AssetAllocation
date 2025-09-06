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
- **Unit Testing**: 29+ test cases ensuring code reliability

### 🛠️ Developer Experience
- **Modular Architecture**: Clean separation of concerns with strategy classes
- **Configuration Management**: Centralized configuration with environment variables
- **CLI Interface**: Command-line tool with multiple output formats
- **Type Hints**: Full type annotation for better code maintainability

### 📊 Output Formats
- **Text**: Human-readable format for console output
- **JSON**: Machine-readable format for API integration
- **CSV**: Spreadsheet-compatible format for analysis

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

2. Install dependencies:
```bash
uv sync
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

### 🖥️ Command Line Interface (CLI)

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

# Verbose logging
uv run asset-cli --verbose

# Cache management
uv run asset-cli --cache-stats
uv run asset-cli --clear-cache

# Performance monitoring
uv run asset-cli --performance

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
# Run the main application
uv run python main.py

# Or using the CLI
uv run asset-cli

# Run specific strategy
uv run asset-cli --strategy kaw --output json
```

### 🧪 Testing

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_strategies.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=. --cov-report=html

# Run tests with verbose output
uv run python -m pytest tests/ -v --tb=short
```

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
├── cli.py                 # Command-line interface
├── main.py               # Main application entry point
├── portfolio.py          # Portfolio management functions
├── config.py             # Configuration management
├── strategies/           # Strategy implementations
│   ├── __init__.py
│   ├── base_strategy.py
│   ├── haa_strategy.py
│   ├── korean_all_weather_strategy.py
│   └── ...
├── services/             # Service layer
│   ├── __init__.py
│   ├── data_service.py
│   └── communication_service.py
├── utils/                # Utility modules
│   ├── __init__.py
│   ├── cache_manager.py
│   └── performance_monitor.py
├── tests/                # Unit tests
│   ├── test_strategies.py
│   ├── test_services.py
│   └── test_utils.py
├── cache/                # Cache directory
├── logs/                 # Log files
└── requirements.txt      # Dependencies
```

## 📦 Dependencies

### Core Dependencies
- `yfinance`: Financial data from Yahoo Finance
- `python-telegram-bot`: Telegram bot integration
- `fredapi`: Federal Reserve Economic Data API
- `python-dotenv`: Environment variable management

### Development Dependencies
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Mocking utilities

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is for educational and research purposes.
