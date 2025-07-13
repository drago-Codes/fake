import os
import joblib
from typing import Any, Tuple
# Placeholder for future scikit-learn model
model = None
model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')

# Load the pre-trained machine learning model from the specified path.
# The model is expected to be saved using joblib.
if os.path.exists(model_path):
    try:
        # Attempt to load the model
        model = joblib.load(model_path)
    except Exception as e:
        # Print an error message if the model fails to load
        print(f'Error loading model: {e}')
else:
    # Print a message if the model file does not exist
    print(f'Model file not found at {model_path}. Using fallback logic.')

def classify_product(
    text_similarity: float,
    image_similarity: float,
    price_deviation: float,
    known_seller: int,
    num_reviews: int,
    avg_rating: float,
    image_count: int,
    desc_length: int,
    keyword_original: int,
    keyword_replica: int,
    keyword_genuine: int
) -> Tuple[int, str]:
    """
    Classify a product as genuine or fake based on features.
    Returns (score, verdict).
    """
    if model:
        X = [[
            text_similarity,
            image_similarity,
            price_deviation,
            known_seller,
            num_reviews,
            avg_rating,
            image_count,
            desc_length,
            keyword_original,
            keyword_replica,
            keyword_genuine
        ]]
        pred = model.predict_proba(X)[0][1]
        score = int(pred * 100)
        verdict = 'Likely Genuine' if score > 60 else 'High Risk'
        return score, verdict
    # Fallback logic if model is not loaded
    score = int((text_similarity * 0.4 + image_similarity * 0.2 + (1 - price_deviation) * 0.2 + known_seller * 0.1 + (avg_rating / 5) * 0.05 + (num_reviews > 50) * 0.05) * 100)
    verdict = 'Likely Genuine' if score > 60 else 'High Risk'
    return score, verdict 