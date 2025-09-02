# Asset Allocation Portfolio Management

A Python application for implementing various asset allocation strategies including Bold Asset Allocation (BAA), Modified Dual Momentum (MDM), Bond Dynamic Asset Allocation (BDAA), and Hybrid Asset Allocation (HAA).

## Features

- **Bold Asset Allocation (BAA)**: Momentum-based strategy with risk management
- **Modified Dual Momentum (MDM)**: Enhanced dual momentum strategy
- **Bond Dynamic Asset Allocation (BDAA)**: Dynamic bond allocation based on performance
- **Hybrid Asset Allocation (HAA)**: Hybrid approach combining multiple factors
- **Telegram Integration**: Automated portfolio updates via Telegram bot
- **FRED API Integration**: Economic data integration (optional)

## Installation

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

Run the main application:
```bash
uv run main.py
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

## Dependencies

- `yfinance`: Financial data from Yahoo Finance
- `python-telegram-bot`: Telegram bot integration
- `fredapi`: Federal Reserve Economic Data API
- `python-dotenv`: Environment variable management

## License

This project is for educational and research purposes.
