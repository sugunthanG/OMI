import joblib
import os

def load_model(path="models/gold_model_v2.pkl"):
    """
    Loads model from given path.
    Supports:
    - raw model
    - dict format {"model": model, "features": [...]}
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Model not found: {path}")

    data = joblib.load(path)

    # If saved as dict (recommended)
    if isinstance(data, dict):
        return data.get("model", data)

    return data