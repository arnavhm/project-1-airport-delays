import sys
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OrdinalEncoder

# Add project root to sys.path to allow imports from src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.pipeline import load_and_preprocess_data
from src.evaluation.validation import validate_model

def train_and_serialize():
    print("🚀 [Training Orchestrator] Starting ML Pipeline...")
    
    # 1. Modular Data Loading (Zero Skew)
    print("   -> Loading data from shared pipeline...")
    df, config = load_and_preprocess_data()
    
    target_col = config["model"]["target_column"]
    cat_cols = config["model"]["categorical_features"]
    num_cols = config["model"]["numeric_features"]
    
    X = df[cat_cols + num_cols]
    y = df[target_col].values
    
    # 2. Data Leakage Guards
    print("   -> Splitting data to prevent leakage...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=config["model"]["test_size"], 
        random_state=config["model"]["random_state"]
    )
    
    # We use HistGradientBoostingRegressor which handles categoricals natively!
    # But we still need a pipeline for scaling numeric features.
    print("   -> Constructing scikit-learn Pipeline...")
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), cat_cols)
        ],
        remainder='drop'
    )
    
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', HistGradientBoostingRegressor(
            random_state=config["model"]["random_state"],
            max_iter=100
        ))
    ])
    
    # 3. Training
    print(f"   -> Training HistGradientBoostingRegressor on {len(X_train)} samples...")
    model.fit(X_train, y_train)
    
    # 4. Evaluation & Safety Gates
    print("   -> Running Safety & Quality Gates on Test Set...")
    y_pred = model.predict(X_test)
    
    passed = validate_model(y_test, y_pred, config)
    
    if passed:
        artifact_path = "artifacts/model_pipeline.joblib"
        print(f"   -> Serializing model pipeline to {artifact_path}...")
        joblib.dump(model, artifact_path)
        print("✅ [Training Orchestrator] Completed Successfully.")
    else:
        print("❌ [Training Orchestrator] Aborted serialization due to safety gate failure.")
        sys.exit(1)

if __name__ == "__main__":
    train_and_serialize()
