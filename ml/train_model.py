import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, KFold
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
import joblib
import numpy as np

# Define the absolute path for the data file
DATA_FILE_PATH = '/home/runner/work/AppSec_finalProject/AppSec_finalProject/data/labeling_template.csv'
# Define the absolute path for saving the trained model
MODEL_SAVE_PATH = '/home/runner/work/AppSec_finalProject/AppSec_finalProject/ml/model.pkl'


def load_data(filepath):
    """Loads the labeled data from a CSV file."""
    try:
        df = pd.read_csv(filepath)
        return df
    except FileNotFoundError:
        print(f"Error: Data file not found at {filepath}")
        exit(1)
    except Exception as e:
        print(f"Error loading data: {e}")
        exit(1)

# Load labeled data
df = load_data(DATA_FILE_PATH)

# Add new features if present
feature_cols = ['text_similarity', 'image_similarity', 'price_deviation', 'known_seller']
for col in ['num_reviews', 'avg_rating', 'image_count', 'desc_length']:
    if col in df.columns:
        feature_cols.append(col)

# Add keyword flags as features if they exist in the dataframe
for k in ['original', 'replica', '100% genuine']:
    col = f'keyword_{k.replace(" ", "_")}'
    if col in df.columns:
        feature_cols.append(col)

# Prepare features (X) and target (y)
X = df[feature_cols]
y = df['label'].str.strip().str.lower().map({'genuine': 1, 'fake': 0})

# Check for unmapped labels
if y.isnull().any():
    print("Error: Found unmapped labels in the 'label' column:", df['label'][y.isnull()])
    exit(1)
# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define the model
model = RandomForestClassifier(random_state=42, class_weight='balanced')

# Hyperparameter tuning using GridSearchCV
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

grid_search = GridSearchCV(model, param_grid, cv=5, scoring='f1', n_jobs=-1)
grid_search.fit(X_train, y_train)

print("Best parameters found: ", grid_search.best_params_)
best_model = grid_search.best_estimator_

# Cross-validation on the best model
cv_scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring='f1')
print(f"Cross-validation F1 scores: {cv_scores}")
print(f"Mean cross-validation F1 score: {np.mean(cv_scores)}")

# Evaluate the best model on the test set
y_pred = best_model.predict(X_test)
print(classification_report(y_test, y_pred))

print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
print(f"Precision: {precision_score(y_test, y_pred)}")
print(f"Recall: {recall_score(y_test, y_pred)}")
print(f"F1-score: {f1_score(y_test, y_pred)}")

# Save the best model
joblib.dump(best_model, '/home/runner/work/AppSec_finalProject/AppSec_finalProject/ml/model.pkl')