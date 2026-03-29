"""
===================================================================================
AI STOCK MARKET SENTIMENT ANALYZER - PRODUCTION PREDICTION ENGINE
===================================================================================
Purpose: Load trained model and generate real-time predictions for production use
         (without running notebook each time)

Usage:
    python production_predictor.py

Requires:
    - models/best_model.pkl (trained model)
    - models/scaler.pkl (feature scaler)
    - models/features.pkl (feature names)
    - Latest sentiment data from data/reports/sentiment_decisions_1year.csv

Author: AI Stock Sentiment System
Date: 2026-03-27
===================================================================================
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ==================================================================================
# CONFIGURATION
# ==================================================================================

BASE_PATH = Path.cwd()
MODEL_PATH = BASE_PATH / 'models' / 'best_model.pkl'
SCALER_PATH = BASE_PATH / 'models' / 'scaler.pkl'
FEATURES_PATH = BASE_PATH / 'models' / 'features.pkl'
DATA_PATH = BASE_PATH / 'data' / 'reports' / 'sentiment_decisions_1year.csv'
OUTPUT_PATH = BASE_PATH / 'predictions'

OUTPUT_PATH.mkdir(exist_ok=True)

# ==================================================================================
# LOAD MODEL & ARTIFACTS
# ==================================================================================

def load_model():
    """Load trained model, scaler, and features from disk."""
    
    print("[INFO] Loading model artifacts...")
    
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    if not SCALER_PATH.exists():
        raise FileNotFoundError(f"Scaler not found: {SCALER_PATH}")
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Features not found: {FEATURES_PATH}")
    
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    
    with open(FEATURES_PATH, 'rb') as f:
        features = pickle.load(f)
    
    print(f"[OK] Model loaded: {type(model).__name__}")
    print(f"[OK] Features: {features}")
    
    return model, scaler, features


# ==================================================================================
# LOAD LATEST DATA
# ==================================================================================

def load_latest_data():
    """Load and prepare latest sentiment data."""
    
    print(f"\n[INFO] Loading latest data from {DATA_PATH}...")
    
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Get latest row per ticker
    latest = df.groupby('ticker').tail(1).reset_index(drop=True)
    
    print(f"[OK] Loaded {len(latest)} tickers")
    print(f"[OK] Latest date: {latest['date'].max().date()}")
    
    return latest


# ==================================================================================
# PREDICTION ENGINE
# ==================================================================================

def predict_signal(features_dict, model, scaler, feature_cols):
    """
    Generate trading signal from features.
    
    Args:
        features_dict (dict): Input features {sentiment, return_1d, momentum, volatility}
        model: Trained ML model
        scaler: Feature scaler
        feature_cols (list): Feature column names
    
    Returns:
        dict: {signal, probability, confidence}
    """
    
    # Prepare features
    X = np.array([features_dict.get(col, 0.0) for col in feature_cols]).reshape(1, -1)
    
    # Scale
    X_scaled = scaler.transform(X)
    
    # Predict
    probability = model.predict_proba(X_scaled)[0][1]
    confidence = abs(probability - 0.5) * 2
    
    # Generate signal
    if probability > 0.60:
        signal = "BUY"
    elif probability < 0.40:
        signal = "SELL"
    else:
        signal = "HOLD"
    
    return {
        'signal': signal,
        'probability': float(probability),
        'confidence': float(confidence),
        'recommendation_strength': 'Strong' if confidence > 0.4 else 'Weak'
    }


# ==================================================================================
# BATCH PREDICTIONS
# ==================================================================================

def predict_all_tickers(data, model, scaler, feature_cols):
    """Generate predictions for all tickers."""
    
    print(f"\n[INFO] Generating predictions for {len(data)} tickers...")
    
    predictions = []
    
    for idx, row in data.iterrows():
        # Prepare features
        features_dict = {
            'sentiment': float(row.get('sentiment', 0.0)),
            'return_1d': float(row.get('return_1d', 0.0)),
            'momentum': float(row.get('momentum', 0.0)),
            'volatility': float(row.get('volatility', 0.0))
        }
        
        # Predict
        pred = predict_signal(features_dict, model, scaler, feature_cols)
        
        # Add to results
        predictions.append({
            'ticker': row['ticker'],
            'date': row['date'],
            'close': float(row['Close']),
            'sentiment': float(row.get('sentiment', 0.0)),
            'return_1d': float(row.get('return_1d', 0.0)),
            'momentum': float(row.get('momentum', 0.0)),
            'volatility': float(row.get('volatility', 0.0)),
            'signal': pred['signal'],
            'probability': pred['probability'],
            'confidence': pred['confidence'],
            'strength': pred['recommendation_strength']
        })
    
    predictions_df = pd.DataFrame(predictions).sort_values('probability', ascending=False)
    
    print(f"[OK] Generated {len(predictions_df)} predictions")
    
    return predictions_df


# ==================================================================================
# GENERATE REPORTS
# ==================================================================================

def generate_summary(predictions_df):
    """Print trading summary."""
    
    print("\n" + "="*80)
    print("TRADING SIGNALS SUMMARY")
    print("="*80)
    
    print(f"\n📊 Signal Distribution:")
    print(f"  BUY signals:  {(predictions_df['signal'] == 'BUY').sum():3d} ({(predictions_df['signal'] == 'BUY').sum() / len(predictions_df) * 100:5.1f}%)")
    print(f"  SELL signals: {(predictions_df['signal'] == 'SELL').sum():3d} ({(predictions_df['signal'] == 'SELL').sum() / len(predictions_df) * 100:5.1f}%)")
    print(f"  HOLD signals: {(predictions_df['signal'] == 'HOLD').sum():3d} ({(predictions_df['signal'] == 'HOLD').sum() / len(predictions_df) * 100:5.1f}%)")
    
    print(f"\n💪 Strong Signals (Confidence > 0.4):")
    strong = predictions_df[predictions_df['confidence'] > 0.4].sort_values('confidence', ascending=False)
    if len(strong) > 0:
        for _, row in strong.head(10).iterrows():
            print(f"  {row['ticker']:12s} → {row['signal']:4s} | Conf: {row['confidence']:.3f} | Prob: {row['probability']:.4f}")
    else:
        print("  (None - all signals below confidence threshold)")
    
    print(f"\n📈 Current Status by Ticker:")
    for _, row in predictions_df.head(5).iterrows():
        print(f"  {row['ticker']:12s} | Close: ${row['close']:8.2f} | Signal: {row['signal']:4s} | Conf: {row['confidence']:.3f}")
    
    print(f"\n" + "="*80)


def export_results(predictions_df):
    """Export predictions to CSV."""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # All predictions
    all_path = OUTPUT_PATH / f'predictions_{timestamp}.csv'
    predictions_df.to_csv(all_path, index=False)
    print(f"\n[OK] Saved all predictions: {all_path}")
    
    # High confidence signals only
    high_conf = predictions_df[
        (predictions_df['confidence'] > 0.3) & 
        (predictions_df['signal'] != 'HOLD')
    ]
    
    if len(high_conf) > 0:
        high_conf_path = OUTPUT_PATH / f'strong_signals_{timestamp}.csv'
        high_conf.to_csv(high_conf_path, index=False)
        print(f"[OK] Saved strong signals: {high_conf_path}")
    
    # Buy signals only
    buy_signals = predictions_df[predictions_df['signal'] == 'BUY']
    if len(buy_signals) > 0:
        buy_path = OUTPUT_PATH / f'buy_signals_{timestamp}.csv'
        buy_signals.to_csv(buy_path, index=False)
        print(f"[OK] Saved buy signals: {buy_path}")
    
    # Sell signals only
    sell_signals = predictions_df[predictions_df['signal'] == 'SELL']
    if len(sell_signals) > 0:
        sell_path = OUTPUT_PATH / f'sell_signals_{timestamp}.csv'
        sell_signals.to_csv(sell_path, index=False)
        print(f"[OK] Saved sell signals: {sell_path}")


# ==================================================================================
# REAL-TIME PREDICTION FUNCTION
# ==================================================================================

def predict_from_features(sentiment, return_1d, momentum, volatility, 
                          model=None, scaler=None, features=None):
    """
    Generate prediction from raw feature values.
    
    Usage:
        result = predict_from_features(
            sentiment=0.15,
            return_1d=0.02,
            momentum=2.5,
            volatility=0.018
        )
        print(result)  # {'signal': 'BUY', 'probability': 0.72, 'confidence': 0.44}
    
    Args:
        sentiment (float): Sentiment score (-1 to +1)
        return_1d (float): 1-day return
        momentum (float): Momentum indicator
        volatility (float): Volatility measure
        model: Trained model (loads if None)
        scaler: Feature scaler (loads if None)
        features: Feature names (loads if None)
    
    Returns:
        dict: {signal, probability, confidence, recommendation_strength}
    """
    
    # Load if not provided
    if model is None or scaler is None or features is None:
        model, scaler, features = load_model()
    
    # Predict
    features_dict = {
        'sentiment': sentiment,
        'return_1d': return_1d,
        'momentum': momentum,
        'volatility': volatility
    }
    
    return predict_signal(features_dict, model, scaler, features)


# ==================================================================================
# MAIN EXECUTION
# ==================================================================================

def main():
    """Execute production prediction pipeline."""
    
    print("\n" + "="*80)
    print("AI STOCK MARKET SENTIMENT ANALYZER - PRODUCTION PREDICTIONS")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load model
    model, scaler, feature_cols = load_model()
    
    # Load latest data
    data = load_latest_data()
    
    # Generate predictions
    predictions_df = predict_all_tickers(data, model, scaler, feature_cols)
    
    # Generate summary
    generate_summary(predictions_df)
    
    # Export results
    export_results(predictions_df)
    
    print(f"\n[OK] EXECUTION COMPLETE")
    print(f"[OK] All predictions saved to: {OUTPUT_PATH}")
    
    return predictions_df


# ==================================================================================
# EXAMPLE USAGE
# ==================================================================================

if __name__ == "__main__":
    
    # Run full pipeline
    predictions_df = main()
    
    # Example: Predict from custom features
    print("\n" + "="*80)
    print("EXAMPLE: REAL-TIME PREDICTION")
    print("="*80)
    
    example_result = predict_from_features(
        sentiment=0.15,      # Positive sentiment
        return_1d=0.02,      # +2% yesterday
        momentum=2.5,        # Upward momentum
        volatility=0.018     # Moderate volatility
    )
    
    print(f"\nInput: sentiment=0.15, return_1d=0.02, momentum=2.5, volatility=0.018")
    print(f"Prediction: {example_result}")
    print(f"Signal: {example_result['signal']}")
    print(f"Confidence: {example_result['confidence']:.1%}")
