# Technical Indicator Feature - Implementation Guide

## Overview

This document describes the Technical Indicator feature added to the PulseAlpha stock dashboard. The feature provides real-time technical analysis using RSI, MACD, and EMA calculations.

## Architecture

### Backend (Python/Flask)

**Service: `backend/services/technical_service.py`**
- `TechnicalIndicatorService` - Main service class
- `TechnicalIndicators` - Data class for indicator results
- Supports both `pandas-ta` library (primary) and fallback manual RSI calculation

**Key Methods:**
- `calculate_indicators(ticker)` - Calculate all technical indicators for a ticker
- `_load_stock_data(ticker)` - Load CSV data from raw or processed files
- `_generate_signal(rsi, macd, histogram)` - Generate Buy/Hold/Sell signal
- `_calculate_simple_rsi(prices, period)` - Fallback RSI without external library
- `list_supported_tickers()` - Return all available tickers

**API Endpoints:**
```
GET  /api/technical/<ticker>
     Returns: Technical indicators with signal and explanation
     Status: 200 OK or 404 Not Found

GET  /api/technical/supported
     Returns: List of supported tickers with count
     Status: 200 OK
```

### Frontend (React/JavaScript)

**Component: `src/components/common/TechnicalIndicatorCard.jsx`**
- Full display mode (comprehensive technical analysis)
- Compact mode (minimal space indicator card)
- Loading states with LoadingSkeleton
- Error handling with user-friendly messages
- Animations using Framer Motion

**Service: `src/services/publicService.js`**
- `getTechnicalIndicators(ticker)` - Fetch indicators for a ticker
- `getSupportedTickers()` - Fetch list of supported tickers

**Integration Points:**
- `CompanyDetailPage` - Full technical analysis for selected stock
- Can be added to `MarketOverviewPage` or `DashboardHomePage` as needed

## Signal Logic

### Buy Signal (RSI < 30)
- Indicates **oversold** conditions
- Potential bounce or reversal
- Stronger if MACD histogram is positive (uptrend confirmation)

### Sell Signal (RSI > 70)
- Indicates **overbought** conditions
- Potential pullback or reversal
- Stronger if MACD histogram is negative (downtrend confirmation)

### Hold Signal (30 ≤ RSI ≤ 70)
- Default neutral condition
- Can have upside or downside bias based on MACD
- Safest signal when RSI and MACD disagree

## Technical Indicators

### RSI (Relative Strength Index)
- **Period**: 14 days (standard)
- **Range**: 0-100
- **Oversold**: < 30
- **Overbought**: > 70
- **Neutral**: 30-70

### MACD (Moving Average Convergence Divergence)
- **Fast EMA Period**: 12 days
- **Slow EMA Period**: 26 days
- **Signal Line Period**: 9 days
- **Components**: MACD line, Signal line, Histogram (MACD - Signal)

### EMA (Exponential Moving Averages)
- **EMA-12**: Short-term trend (12-day)
- **EMA-26**: Long-term trend (26-day)
- **Usage**: EMA-12 > EMA-26 suggests uptrend

## Data Flow

### Calculation Process
1. Load stock CSV from `data/raw/` or `data/processed/`
2. Extract Close prices
3. Calculate RSI using 14-period average gains/losses
4. Calculate MACD (12/26/9) from Close prices
5. Calculate EMA-12 and EMA-26
6. Generate signal based on RSI + optional MACD confirmation
7. Return as JSON API response

### Data Validation
- Requires minimum 15 data points for RSI calculation
- Handles missing/null values gracefully
- Falls back to manual RSI if pandas-ta unavailable
- Returns error 404 if ticker not found

## Usage Examples

### Python Backend
```python
from backend.services.technical_service import TechnicalIndicatorService

service = TechnicalIndicatorService()
indicators = service.calculate_indicators("AAPL")

if indicators:
    print(f"RSI: {indicators.rsi}")
    print(f"Signal: {indicators.buy_sell_signal}")
    print(f"Explanation: {indicators.explanation}")
```

### JavaScript/React Frontend
```javascript
import { getTechnicalIndicators } from "../../services/publicService";

async function loadTechnicalData(ticker) {
  try {
    const data = await getTechnicalIndicators(ticker);
    console.log(data);
    // data.rsi, data.macd, data.signal, etc.
  } catch (error) {
    console.error(error.message);
  }
}
```

### React Component Usage
```jsx
import { TechnicalIndicatorCard } from "../../components/common/TechnicalIndicatorCard";

// Full display mode
<TechnicalIndicatorCard ticker="AAPL" />

// Compact mode
<TechnicalIndicatorCard ticker="AAPL" compact={true} />
```

## API Response Format

```json
{
  "ticker": "AAPL",
  "date": "2024-03-29",
  "closePrice": 173.31,
  "rsi": 45.2,
  "rsiStatus": "Neutral",
  "macd": 0.0234,
  "signalLine": 0.0198,
  "histogram": 0.0036,
  "ema12": 172.54,
  "ema26": 171.89,
  "signal": "HOLD",
  "explanation": "RSI neutral (45.2) but MACD positive - slight upside bias",
  "taStatus": "ready"
}
```

## Installation & Setup

### Backend
1. Install pandas-ta-classic:
   ```bash
   cd backend
   pip install pandas-ta>=0.3.0b0
   ```

2. Verify import works:
   ```bash
   python -c "import pandas_ta; print('Success')"
   ```

3. Feature automatically loads on app startup

### Frontend
1. No additional dependencies needed (uses existing apiClient)
2. Component ready to use after integration

## Performance Considerations

**Calculation Time**: ~50-200ms per ticker (depends on data size)
**Cache Strategy**: None (always fresh from CSV)
**Memory Usage**: Minimal (only loaded ticker in memory at a time)

## Error Handling

| Error | Cause | Handling |
|-------|-------|----------|
| Ticker not found | No CSV file for ticker | Return 404 |
| Invalid ticker | Empty string | Return 400 |
| Calculation error | Corrupted data | Return None, fallback to simple RSI |
| pandas-ta unavailable | Not installed | Use fallback manual calculation |

## Future Enhancements

1. **Additional Indicators**
   - Bollinger Bands
   - Stochastic Oscillator
   - Volume analysis

2. **Advanced Signals**
   - Moving average crossovers
   - Support/resistance levels
   - Divergence detection

3. **Caching**
   - Redis cache for frequently requested tickers
   - TTL-based refresh (e.g., daily)

4. **Historical Signals**
   - Track signal accuracy over time
   - Backtest signal effectiveness
   - Win rate statistics

## Testing

### Backend Test Example
```bash
# Test stock data loading
curl http://localhost:5000/api/technical/AAPL

# Test supported tickers
curl http://localhost:5000/api/technical/supported

# Test invalid ticker
curl http://localhost:5000/api/technical/INVALID
```

### Frontend Component Test
```jsx
// In React component
import { render, screen } from "@testing-library/react";
import { TechnicalIndicatorCard } from "./TechnicalIndicatorCard";

test("renders ticker", async () => {
  render(<TechnicalIndicatorCard ticker="AAPL" />);
  await screen.findByText("AAPL");
});
```

## Troubleshooting

**Issue**: "pandas-ta-classic not installed"
- Solution: `pip install pandas-ta>=0.3.0b0`

**Issue**: No technical data appears
- Check: CSV files exist in `data/raw/` or `data/processed/`
- Check: Browser console for fetch errors
- Check: API endpoint accessibility

**Issue**: RSI always shows ~50
- Cause: Insufficient data points
- Solution: Ensure CSV has 15+ rows of data

**Issue**: Component doesn't load
- Check: Ticker prop is provided
- Check: apiClient is working
- Check: Network tab for failed requests

## Security & Privacy

- No authentication required (uses public API)
- No personal data collected
- Rate limiting not implemented (consider for production)
- CSV data is read-only

## License & Attribution

Technical indicator formulas based on standard financial practices. Suitable for educational and research purposes.

## Support

For issues or questions:
1. Check this guide
2. Review error messages in console
3. Verify CSV data format
4. Check backend logs
