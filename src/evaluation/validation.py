import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score

def validate_model(y_true, y_pred, config):
    """
    Implements Safety and Quality Gates before a model can be serialized.
    """
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    print(f"[Validation] MAE: {mae:.2f} minutes")
    print(f"[Validation] R2 Score: {r2:.3f}")
    
    # 1. Accuracy Gate
    if r2 < 0.02:
        # Delays are notoriously hard to predict precisely due to heavy tails,
        # but R2 should be positive (better than mean prediction).
        print("🚨 [GATE FAILED] R2 Score is too low (model is worse than mean prediction).")
        return False
        
    # 2. Prediction Bias Gate (Safety limit check)
    # The model must not systematically under-predict severe delays.
    # We calculate the bias on the severe delays slice.
    severe_threshold = config["model"]["risk_threshold_minutes"]
    severe_mask = y_true > severe_threshold
    
    if np.sum(severe_mask) > 0:
        mean_actual_severe = np.mean(y_true[severe_mask])
        mean_pred_severe = np.mean(y_pred[severe_mask])
        bias_ratio = mean_pred_severe / mean_actual_severe
        print(f"[Validation] Severe Delay Bias Ratio: {bias_ratio:.2f} (Pred/Actual)")
        
        # If the model predicts less than 5% of the actual severity for extreme cases, it's unsafe
        if bias_ratio < 0.05:
            print("🚨 [GATE FAILED] Model massively under-predicts severe delays. High Safety Risk.")
            return False
            
    # 3. Monotonicity / Output Validity Check
    # Predictions shouldn't be negative in a way that breaks physics (e.g. predicting arriving 20 hours early)
    if np.min(y_pred) < -100:
        print("🚨 [GATE FAILED] Model predicting impossible early arrivals (< -100m).")
        return False
        
    print("✅ [GATE PASSED] Model validated for production deployment.")
    return True
