"""
===================================================================================
AI STOCK MARKET SENTIMENT ANALYZER - ML MODEL PIPELINE
===================================================================================
Purpose: Train multiple ML models, compare performance, save best model, and 
         provide prediction functions.

Data Source: data/reports/sentiment_decisions_1year.csv
Models: Logistic Regression, Random Forest, XGBoost
Output: models/model.pkl, models/features.pkl, evaluation_results.csv

Author: AI Stock Sentiment System
Date: 2026-03-27
===================================================================================
"""

import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import warnings
warnings.filterwarnings('ignore')

# ML imports
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, classification_report
import xgboost as xgb

# For reproducibility
np.random.seed(42)

# ==================================================================================
# 1. CONFIGURATION & PATHS
# ==================================================================================

DATA_PATH = Path("data/reports/sentiment_decisions_1year.csv")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

FEATURES = ["sentiment", "return_1d", "momentum", "volatility"]
TEST_SIZE = 0.2
RANDOM_STATE = 42

# ==================================================================================
# 2. DATA LOADING & PREPARATION
# ==================================================================================

def load_and_prepare_data():
    """
    Load sentiment data and create target variable.
    
    Steps:
    1. Load CSV
    2. Handle missing values
    3. Create target: 1 if next day Close > current Close, else 0
    4. Prepare features
    
    Returns:
        X (pd.DataFrame): Features
        y (pd.Series): Target variable
        feature_columns (list): Names of feature columns
    """
    print("[INFO] Loading sentiment data...")
    df = pd.read_csv(DATA_PATH)
    
    # Sort by ticker and date
    df = df.sort_values(by=["ticker", "date"])
    
    print(f"[OK] Loaded {len(df)} rows")
    
    # Create target: 1 if next day's Close > current Close
    df["target"] = (df.groupby("ticker")["Close"].shift(-1) > df["Close"]).astype(int)
    
    # Remove last row per ticker (no next day data)
    df = df[df["target"].notna()]
    
    print(f"[INFO] Target variable created: {len(df)} rows with valid targets")
    
    # Handle missing values
    print("[INFO] Handling missing values...")
    
    # For sentiment: fill with 0 (neutral)
    df["sentiment"] = df["sentiment"].fillna(0.0)
    
    # For return_1d: fill with 0 (no change)
    df["return_1d"] = df["return_1d"].fillna(0.0)
    
    # For momentum and volatility: forward fill, then backward fill
    df["momentum"] = df.groupby("ticker")["momentum"].fillna(method="ffill").fillna(method="bfill").fillna(0.0)
    df["volatility"] = df.groupby("ticker")["volatility"].fillna(method="ffill").fillna(method="bfill").fillna(0.0)
    
    print(f"[OK] Missing values handled")
    print(f"[INFO] Data shape after cleaning: {df.shape}")
    
    # Prepare features and target
    X = df[FEATURES].copy()
    y = df["target"].copy()
    
    print(f"[INFO] Features: {FEATURES}")
    print(f"[INFO] Target distribution: {y.value_counts().to_dict()}")
    print(f"[INFO] Class balance: {(y.value_counts() / len(y) * 100).to_dict()}")
    
    return X, y, FEATURES


# ==================================================================================
# 3. FEATURE SCALING
# ==================================================================================

def scale_features(X_train, X_test):
    """
    Normalize features using StandardScaler.
    
    Args:
        X_train (pd.DataFrame): Training features
        X_test (pd.DataFrame): Test features
    
    Returns:
        X_train_scaled (np.ndarray): Scaled training features
        X_test_scaled (np.ndarray): Scaled test features
        scaler (StandardScaler): Fitted scaler for production use
    """
    print("[INFO] Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("[OK] Features scaled")
    return X_train_scaled, X_test_scaled, scaler


# ==================================================================================
# 4. MODEL TRAINING
# ==================================================================================

def train_models(X_train, X_test, y_train, y_test):
    """
    Train multiple models and evaluate on test set.
    
    Models:
    1. Logistic Regression
    2. Random Forest
    3. XGBoost
    
    Args:
        X_train (np.ndarray): Scaled training features
        X_test (np.ndarray): Scaled test features
        y_train (pd.Series): Training labels
        y_test (pd.Series): Test labels
    
    Returns:
        models (dict): Trained models
        results (dict): Evaluation metrics
    """
    print("\n" + "="*80)
    print("MODEL TRAINING")
    print("="*80)
    
    models = {}
    results = {}
    
    # ========== 1. LOGISTIC REGRESSION ==========
    print("\n[INFO] Training Logistic Regression...")
    lr_model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    lr_model.fit(X_train, y_train)
    models["Logistic Regression"] = lr_model
    y_pred_lr = lr_model.predict(X_test)
    y_proba_lr = lr_model.predict_proba(X_test)[:, 1]
    
    results["Logistic Regression"] = evaluate_model(
        y_test, y_pred_lr, y_proba_lr, "Logistic Regression"
    )
    
    # ========== 2. RANDOM FOREST ==========
    print("\n[INFO] Training Random Forest...")
    rf_model = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    models["Random Forest"] = rf_model
    y_pred_rf = rf_model.predict(X_test)
    y_proba_rf = rf_model.predict_proba(X_test)[:, 1]
    
    results["Random Forest"] = evaluate_model(
        y_test, y_pred_rf, y_proba_rf, "Random Forest"
    )
    
    # ========== 3. XGBOOST ==========
    print("\n[INFO] Training XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=100, 
        max_depth=5, 
        learning_rate=0.1,
        random_state=RANDOM_STATE,
        verbosity=0
    )
    xgb_model.fit(X_train, y_train, verbose=False)
    models["XGBoost"] = xgb_model
    y_pred_xgb = xgb_model.predict(X_test)
    y_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
    
    results["XGBoost"] = evaluate_model(
        y_test, y_pred_xgb, y_proba_xgb, "XGBoost"
    )
    
    return models, results


# ==================================================================================
# 5. MODEL EVALUATION
# ==================================================================================

def evaluate_model(y_test, y_pred, y_proba, model_name):
    """
    Evaluate model performance.
    
    Metrics:
    - Accuracy
    - Precision (% of predicted positives that are correct)
    - Recall (% of actual positives that were identified)
    - Confusion matrix
    
    Args:
        y_test (pd.Series): True labels
        y_pred (np.ndarray): Predicted labels
        y_proba (np.ndarray): Predicted probabilities
        model_name (str): Name of model
    
    Returns:
        metrics (dict): Evaluation metrics
    """
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    print(f"\n[EVAL] {model_name}")
    print(f"  Accuracy:  {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  True Neg:  {tn}")
    print(f"  False Pos: {fp}")
    print(f"  False Neg: {fn}")
    print(f"  True Pos:  {tp}")
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "y_pred": y_pred,
        "y_proba": y_proba
    }


def compare_models(results):
    """
    Compare all models and select best.
    
    Selection criteria:
    1. Highest accuracy
    2. Secondarily: prefer Random Forest for interpretability
    
    Args:
        results (dict): Evaluation results for all models
    
    Returns:
        best_model_name (str): Name of best model
        comparison_df (pd.DataFrame): Comparison table
    """
    print("\n" + "="*80)
    print("MODEL COMPARISON")
    print("="*80)
    
    # Create comparison dataframe
    comparison_data = []
    for model_name, metrics in results.items():
        comparison_data.append({
            "Model": model_name,
            "Accuracy": metrics["accuracy"],
            "Precision": metrics["precision"],
            "Recall": metrics["recall"],
            "TP": metrics["tp"],
            "TN": metrics["tn"],
            "FP": metrics["fp"],
            "FN": metrics["fn"]
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df = comparison_df.sort_values("Accuracy", ascending=False)
    
    print("\n" + comparison_df.to_string(index=False))
    
    # Select best model
    best_model_name = comparison_df.iloc[0]["Model"]
    print(f"\n[OK] Best Model: {best_model_name} (Accuracy: {comparison_df.iloc[0]['Accuracy']:.4f})")
    
    return best_model_name, comparison_df


# ==================================================================================
# 6. FEATURE IMPORTANCE (for Random Forest)
# ==================================================================================

def get_feature_importance(model, feature_names):
    """
    Extract feature importance from tree-based models.
    
    Args:
        model: Trained model (Random Forest or XGBoost)
        feature_names (list): Names of features
    
    Returns:
        importance_df (pd.DataFrame): Feature importance ranking
    """
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        importance_df = pd.DataFrame({
            "Feature": feature_names,
            "Importance": importances
        }).sort_values("Importance", ascending=False)
        
        print("\n[INFO] Feature Importance:")
        print(importance_df.to_string(index=False))
        
        return importance_df
    return None


# ==================================================================================
# 7. SAVE MODEL & ARTIFACTS
# ==================================================================================

def save_model(model, feature_columns, scaler, model_name):
    """
    Save trained model and artifacts for production use.
    
    Files:
    - models/model.pkl (trained model)
    - models/features.pkl (feature columns)
    - models/scaler.pkl (feature scaler)
    
    Args:
        model: Trained model
        feature_columns (list): Names of features
        scaler: StandardScaler object
        model_name (str): Name of model for logging
    """
    print("\n[INFO] Saving model artifacts...")
    
    # Save model
    model_path = MODEL_DIR / "model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"[OK] Saved model: {model_path}")
    
    # Save feature columns
    features_path = MODEL_DIR / "features.pkl"
    with open(features_path, 'wb') as f:
        pickle.dump(feature_columns, f)
    print(f"[OK] Saved features: {features_path}")
    
    # Save scaler
    scaler_path = MODEL_DIR / "scaler.pkl"
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"[OK] Saved scaler: {scaler_path}")
    
    # Save model metadata
    metadata = {
        "model_name": model_name,
        "features": feature_columns,
        "random_state": RANDOM_STATE,
        "timestamp": pd.Timestamp.now()
    }
    metadata_path = MODEL_DIR / "metadata.pkl"
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"[OK] Saved metadata: {metadata_path}")


# ==================================================================================
# 8. PREDICTION FUNCTION
# ==================================================================================

def load_model_artifacts():
    """
    Load trained model and artifacts from disk.
    
    Returns:
        model: Trained model
        feature_columns (list): Feature names
        scaler: Feature scaler
    """
    model_path = MODEL_DIR / "model.pkl"
    features_path = MODEL_DIR / "features.pkl"
    scaler_path = MODEL_DIR / "scaler.pkl"
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(features_path, 'rb') as f:
        feature_columns = pickle.load(f)
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    return model, feature_columns, scaler


def predict_signal(row, model=None, feature_columns=None, scaler=None):
    """
    Predict trading signal from input features.
    
    Signal Thresholds:
    - BUY: probability > 0.6 (high confidence uptrend)
    - SELL: probability < 0.4 (high confidence downtrend)
    - HOLD: 0.4 <= probability <= 0.6 (neutral zone)
    
    Confidence Score:
    - Range: [0, 1]
    - Formula: abs(probability - 0.5) * 2
    - Confidence in decision vs neutral
    
    Args:
        row (dict or pd.Series): Input features {sentiment, return_1d, momentum, volatility}
        model: Trained model (optional, loads from disk if None)
        feature_columns (list): Feature names (optional, loads from disk if None)
        scaler: Feature scaler (optional, loads from disk if None)
    
    Returns:
        result (dict): {
            "signal": "BUY"/"SELL"/"HOLD",
            "probability": float (0-1),
            "confidence": float (0-1)
        }
    """
    # Load model if not provided
    if model is None:
        model, feature_columns, scaler = load_model_artifacts()
    
    # Convert input to dataframe
    if isinstance(row, dict):
        row = pd.Series(row)
    
    # Prepare features
    if isinstance(row, pd.Series):
        X = row[feature_columns].values.reshape(1, -1)
    else:
        X = row[feature_columns].values.reshape(1, -1)
    
    # Scale features
    X_scaled = scaler.transform(X)
    
    # Predict
    probability = model.predict_proba(X_scaled)[0][1]
    confidence = abs(probability - 0.5) * 2
    
    # Generate signal
    if probability > 0.6:
        signal = "BUY"
    elif probability < 0.4:
        signal = "SELL"
    else:
        signal = "HOLD"
    
    return {
        "signal": signal,
        "probability": float(probability),
        "confidence": float(confidence)
    }


# ==================================================================================
# 9. EXPORT EVALUATION RESULTS
# ==================================================================================

def export_results(comparison_df, importance_df=None):
    """
    Save evaluation results to CSV.
    
    Args:
        comparison_df (pd.DataFrame): Model comparison
        importance_df (pd.DataFrame): Feature importance (optional)
    """
    print("\n[INFO] Exporting evaluation results...")
    
    # Save comparison
    comparison_path = Path("evaluation_results.csv")
    comparison_df.to_csv(comparison_path, index=False)
    print(f"[OK] Saved comparison: {comparison_path}")
    
    # Save feature importance if available
    if importance_df is not None:
        importance_path = Path("feature_importance.csv")
        importance_df.to_csv(importance_path, index=False)
        print(f"[OK] Saved importance: {importance_path}")


# ==================================================================================
# 10. MAIN PIPELINE
# ==================================================================================

def main():
    """
    Execute complete ML pipeline.
    
    Flow:
    1. Load and prepare data
    2. Split train/test
    3. Scale features
    4. Train models
    5. Compare and select best
    6. Extract feature importance
    7. Save model
    8. Export results
    """
    
    print("\n" + "="*80)
    print("AI STOCK MARKET SENTIMENT ANALYZER - ML MODEL PIPELINE")
    print("="*80)
    
    # ========== Load & Prepare Data ==========
    X, y, feature_columns = load_and_prepare_data()
    
    # ========== Train/Test Split ==========
    print("\n[INFO] Splitting data: 80/20 (train/test)")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"[OK] Train: {len(X_train)} | Test: {len(X_test)}")
    
    # ========== Scale Features ==========
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
    
    # ========== Train Models ==========
    models, results = train_models(X_train_scaled, X_test_scaled, y_train, y_test)
    
    # ========== Compare Models ==========
    best_model_name, comparison_df = compare_models(results)
    
    # ========== Feature Importance ==========
    best_model = models[best_model_name]
    importance_df = get_feature_importance(best_model, feature_columns)
    
    # ========== Save Model ==========
    save_model(best_model, feature_columns, scaler, best_model_name)
    
    # ========== Export Results ==========
    export_results(comparison_df, importance_df)
    
    # ========== Test Prediction Function ==========
    print("\n" + "="*80)
    print("TESTING PREDICTION FUNCTION")
    print("="*80)
    
    # Test with sample from test set
    sample_idx = 0
    sample_row = X_test.iloc[sample_idx]
    true_label = y_test.iloc[sample_idx]
    
    prediction = predict_signal(sample_row, best_model, feature_columns, scaler)
    
    print(f"\n[TEST] Sample Row:")
    print(f"  Sentiment:  {sample_row['sentiment']:.4f}")
    print(f"  Return_1d:  {sample_row['return_1d']:.4f}")
    print(f"  Momentum:   {sample_row['momentum']:.4f}")
    print(f"  Volatility: {sample_row['volatility']:.4f}")
    print(f"\n[PREDICTION]")
    print(f"  Signal:     {prediction['signal']}")
    print(f"  Probability: {prediction['probability']:.4f}")
    print(f"  Confidence: {prediction['confidence']:.4f}")
    print(f"  True Label: {'UP (1)' if true_label == 1 else 'DOWN (0)'}")
    
    print("\n" + "="*80)
    print("✓ PIPELINE COMPLETE")
    print("="*80)
    print(f"\n[SUMMARY]")
    print(f"  Best Model:     {best_model_name}")
    print(f"  Best Accuracy:  {comparison_df.iloc[0]['Accuracy']:.4f}")
    print(f"  Model saved to: models/model.pkl")
    print(f"  Results saved to: evaluation_results.csv")
    print(f"  Features saved to: models/features.pkl")
    print(f"  Scaler saved to: models/scaler.pkl")
    print(f"\n[READY FOR INTEGRATION]")
    print(f"  Use predict_signal() function for real-time predictions")
    print(f"  Example: predict_signal({{'sentiment': 0.1, 'return_1d': 0.01, 'momentum': 2.5, 'volatility': 0.02}})")


if __name__ == "__main__":
    main()
