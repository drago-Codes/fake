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
        try:
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
            
            if score >= 80:
                verdict = 'Highly Genuine'
            elif score >= 60:
                verdict = 'Likely Genuine'
            elif score >= 40:
                verdict = 'Suspicious'
            else:
                verdict = 'High Risk'
                
            return score, verdict
        except Exception as e:
            print(f"Model prediction error: {e}")
    
    # Enhanced fallback logic
    try:
        # Normalize inputs
        text_sim = max(0, min(1, text_similarity))
        image_sim = max(0, min(1, image_similarity))
        price_dev = max(0, min(2, price_deviation))  # Cap at 200%
        seller_trust = int(known_seller)
        review_score = min(1, num_reviews / 100)  # Normalize reviews
        rating_score = max(0, min(1, avg_rating / 5))  # Normalize rating
        image_score = min(1, image_count / 5)  # Normalize image count
        desc_score = min(1, desc_length / 500)  # Normalize description length
        
        # Red flags
        red_flags = 0
        if keyword_replica > 0:
            red_flags += 30
        if price_dev > 0.5:  # More than 50% price deviation
            red_flags += 20
        if avg_rating < 2.0 and num_reviews > 10:
            red_flags += 15
        if image_count < 2:
            red_flags += 10
        if desc_length < 50:
            red_flags += 10
            
        # Positive signals
        positive_score = (
            text_sim * 25 +
            image_sim * 20 +
            (1 - min(1, price_dev)) * 15 +
            seller_trust * 15 +
            review_score * 10 +
            rating_score * 10 +
            image_score * 5 +
            desc_score * 5 +
            keyword_genuine * 10 +
            keyword_original * 5
        )
        
        # Final score
        score = max(0, min(100, int(positive_score - red_flags)))
        
        if score >= 80:
            verdict = 'Highly Genuine'
        elif score >= 65:
            verdict = 'Likely Genuine'
        elif score >= 45:
            verdict = 'Suspicious'
        else:
            verdict = 'High Risk'
            
        return score, verdict
        
    except Exception as e:
        print(f"Fallback classification error: {e}")
        return 30, 'High Risk' 