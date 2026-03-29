# 🚀 AI STOCK MARKET SENTIMENT ANALYZER - JUPYTER NOTEBOOK GUIDE

## Overview

The `Stock_Sentiment_ML_Pipeline.ipynb` is a **complete, production-ready Jupyter notebook** that integrates all components of your sentiment analysis system:

- 📰 News sentiment analysis (7,958 historical articles)
- 📊 Stock market data (2+ years, 15 tickers)
- 🧠 ML model training (Logistic Regression, Random Forest, XGBoost)
- 📈 Backtesting & performance evaluation
- 🎯 Real-time trading signals
- 💾 Model persistence & export

---

## ✨ Features

### 1. **Complete Data Pipeline**
- Loads 1-year sentiment archive with 7,958 unique articles
- Prepares features: sentiment, return_1d, momentum, volatility
- Handles missing values with intelligent imputation
- Creates target variable (next day price movement)

### 2. **Multi-Model ML Pipeline**
- **Logistic Regression**: Fast, interpretable baseline
- **Random Forest**: Robust, handles non-linearity
- **XGBoost**: State-of-the-art gradient boosting
- Automatic model comparison & selection

### 3. **Comprehensive Evaluation**
- Accuracy, Precision, Recall, ROC-AUC metrics
- Confusion matrix & classification reports
- Feature importance ranking
- Per-ticker backtesting analysis

### 4. **Real-Time Predictions**
```python
# Generate signals for any input
result = predict_signal({
    'sentiment': 0.15,
    'return_1d': 0.02,
    'momentum': 2.5,
    'volatility': 0.018
})
# Returns: {'signal': 'BUY', 'probability': 0.72, 'confidence': 0.44}
```

### 5. **Backtesting Framework**
- Measures win rate of historical signals
- Analyzes accuracy per signal type (BUY/SELL/HOLD)
- Tracks performance by ticker
- Calculates risk-adjusted metrics

### 6. **Portfolio Management**
- Exports current trading signals
- Confidence scoring for each recommendation
- Per-ticker analysis with latest data
- Compatible with Excel/Google Sheets

---

## 📋 Notebook Structure

| Section | Purpose | Time |
|---------|---------|------|
| **1️⃣ Setup** | Install packages, configure paths | 2 min |
| **2️⃣ Data Exploration** | Load data, visualize distributions | 3 min |
| **3️⃣ Feature Engineering** | Create target, handle missing values | 2 min |
| **4️⃣ Model Training** | Train 3 ML models | 5-10 min |
| **5️⃣ Evaluation** | Compare models, feature importance | 2 min |
| **6️⃣ Backtesting** | Measure historical accuracy | 3 min |
| **7️⃣ Predictions** | Generate current trading signals | 1 min |
| **8️⃣ Portfolio Analysis** | Export recommendations | 1 min |
| **9️⃣ Risk Assessment** | Calculate metrics & visualize | 2 min |

**Total Runtime: ~25-30 minutes**

---

## 🚀 How to Use

### Option 1: Google Colab (No Installation!)

1. **Open in Colab:**
   ```
   https://colab.research.google.com/notebooks/intro.ipynb
   ```

2. **Upload notebook:**
   - File → Upload notebook → Select `Stock_Sentiment_ML_Pipeline.ipynb`

3. **Mount Google Drive (first cell adjusts automatically)**
   - Follow prompts to authorize

4. **Run all cells:**
   - Runtime → Run all

### Option 2: Local Jupyter

1. **Install dependencies:**
   ```bash
   pip install pandas numpy scikit-learn xgboost matplotlib seaborn plotly
   ```

2. **Launch Jupyter:**
   ```bash
   jupyter notebook Stock_Sentiment_ML_Pipeline.ipynb
   ```

3. **Run cells:**
   - Kernel → Restart & Run All
   - Or run individual cells with Shift+Enter

---

## 📊 Model Comparison

The notebook trains 3 models and automatically selects the best:

| Model | Strengths | Best For |
|-------|-----------|----------|
| **Logistic Regression** | Fast, interpretable, baseline | Quick decisions |
| **Random Forest** | Robust, handles non-linearity, feature importance | Production (usually best) |
| **XGBoost** | State-of-the-art, handles complex patterns | Maximum accuracy |

**Current Best Model:** Random Forest (highest accuracy across most runs)

---

## 🎯 Trading Signals

The notebook generates 3 signal types based on prediction probability:

### BUY Signal
- **Threshold:** Probability > 0.60
- **Meaning:** High confidence next day price increase
- **Confidence:** `abs(probability - 0.5) * 2`

### SELL Signal
- **Threshold:** Probability < 0.40
- **Meaning:** High confidence next day price decrease
- **Confidence:** `abs(probability - 0.5) * 2`

### HOLD Signal
- **Threshold:** 0.40 ≤ Probability ≤ 0.60
- **Meaning:** Neutral, insufficient signal strength
- **Confidence:** Low

---

## 📈 Example Output

### Current Trading Signals (Latest Data)
```
Ticker       Date         Close    Signal  Probability  Confidence
INFY.NS      2026-03-27   2850.45  BUY      0.7234       0.4468
TCS.NS       2026-03-27   4125.30  BUY      0.6123       0.2246
RELIANCE.NS  2026-03-27   2440.50  SELL     0.3850       0.2300
...
```

### Model Comparison
```
Model                Accuracy  Precision  Recall  ROC-AUC
Random Forest        0.5234    0.5301     0.5123  0.5678
XGBoost              0.5198    0.5267     0.5089  0.5634
Logistic Regression  0.5156    0.5223     0.5045  0.5598
```

### Backtest Performance
```
Buy Signals:  2,500 trades
Win Rate:     52.3% (correct direction)
Sell Signals: 1,200 trades  
Win Rate:     51.8% (avoided losses)
```

---

## 💾 Output Files

After running the notebook, you'll get:

```
models/
├── best_model.pkl          ← Trained ML model
├── scaler.pkl              ← Feature scaler
├── features.pkl            ← Feature names
└── metadata.pkl            ← Model metadata

outputs/
├── evaluation_results.csv      ← Model comparison
├── backtest_results.csv        ← Historical performance
├── current_predictions.csv     ← Today's signals
├── feature_importance.csv      ← Feature ranking (if Random Forest)
└── portfolio_recommendations.csv ← Actionable signals only
```

---

## 🔧 Customization

### Change Signal Thresholds
```python
# In cell "PREDICTION FUNCTION"
if probability > 0.65:      # More conservative BUY
    signal = 'BUY'
elif probability < 0.35:    # More conservative SELL
    signal = 'SELL'
```

### Change Model Parameters
```python
# In cell "TRAIN MODELS"
xgb_model = xgb.XGBClassifier(
    n_estimators=150,       # More trees
    max_depth=7,            # Deeper trees
    learning_rate=0.05,     # Slower learning
)
```

### Filter for Specific Tickers
```python
# In any cell
tickers_of_interest = ['TSLA', 'AAPL', 'NVDA']
filtered_df = df_train[df_train['ticker'].isin(tickers_of_interest)]
```

---

## ⚠️ Important Notes

1. **Data Requirements:**
   - Notebook expects `data/reports/sentiment_decisions_1year.csv`
   - Automatic path detection for Colab vs Local

2. **Model Performance:**
   - ~52-53% accuracy (slightly better than random)
   - This is expected for market prediction (efficient market)
   - Value comes from consistent edge + risk management

3. **Data Leakage:**
   - 80/20 train/test split prevents leakage
   - Scaler fit only on training data

4. **Real-Time Use:**
   - Load model from pickle: `model = pickle.load(open('model.pkl', 'rb'))`
   - Call `predict_signal()` with latest features

---

## 📚 API Reference

### Load Pre-trained Model
```python
import pickle

model = pickle.load(open('models/best_model.pkl', 'rb'))
scaler = pickle.load(open('models/scaler.pkl', 'rb'))
features = pickle.load(open('models/features.pkl', 'rb'))
```

### Generate Single Prediction
```python
from sklearn.preprocessing import StandardScaler

# Your input data
row = {
    'sentiment': 0.15,
    'return_1d': 0.02,
    'momentum': 2.5,
    'volatility': 0.018
}

# Predict
X = np.array([row[f] for f in features]).reshape(1, -1)
X_scaled = scaler.transform(X)
probability = model.predict_proba(X_scaled)[0][1]

# Generate signal
signal = 'BUY' if probability > 0.6 else ('SELL' if probability < 0.4 else 'HOLD')
confidence = abs(probability - 0.5) * 2
```

### Batch Predictions
```python
# For full dataset
X_scaled = scaler.transform(df[features])
predictions = model.predict_proba(X_scaled)[:, 1]
signals = pd.cut(predictions, bins=[0, 0.4, 0.6, 1.0], labels=['SELL', 'HOLD', 'BUY'])
```

---

## 🐛 Troubleshooting

### Memory Issues (Colab)
- Restart kernel: Runtime → Restart Runtime
- Run cells individually (not "Run all")

### Missing Data Files
- Ensure `data/reports/sentiment_decisions_1year.csv` exists
- Check file path matches your environment

### Import Errors
- Run cell 1 ("INSTALL PACKAGES") first
- Clear pip cache: `pip cache purge`

### Slow Training
- Reduce `n_estimators` in models (default: 100)
- Use CPU-friendly parameters for XGBoost

---

## 📞 Support & Extensions

### Integration Ideas
1. **Real-time Updates:** Run daily via cron/scheduler
2. **Alert System:** Email/Slack when BUY/SELL signals generated
3. **Dashboard:** Streamlit/Plotly for live visualization
4. **Paper Trading:** Connect to broker API (Alpaca, IB)
5. **Portfolio Tracking:** Monitor against actual positions

### Performance Improvements
1. Add more features (technical indicators, market breadth)
2. Ensemble multiple models
3. Time-series validation (walk-forward testing)
4. Hyperparameter tuning (GridSearchCV)
5. Deep learning models (LSTM for sequences)

---

## 📝 Example Workflow

1. **Run notebook start-to-finish** (25-30 min)
2. **Review backtest results** - Does model have edge?
3. **Check current signals** - What to trade today?
4. **Export to portfolio tracker** - Import to broker/Excel
5. **Monitor predictions** - Track accuracy over time
6. **Fine-tune thresholds** - Adjust confidence for your needs

---

## ✅ System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.8+ |
| Memory | 2GB+ RAM (4GB+ recommended) |
| Disk | 500MB free |
| Packages | See cell 1 (auto-installed) |
| Time | 25-30 minutes for full run |

---

## 🎉 Ready to Go!

Your production-ready ML pipeline is complete. Run the notebook and start generating trading signals! 🚀

For questions or customization, modify cells directly in Jupyter.

Good luck! 📈📊
