import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Load labeled data
df = pd.read_csv('data/labeling_template.csv')

# Add new features if present
feature_cols = ['text_similarity', 'image_similarity', 'price_deviation', 'known_seller']
for col in ['num_reviews', 'avg_rating', 'image_count', 'desc_length']:
    if col in df.columns:
        feature_cols.append(col)
# Add keyword flags as features if present
for k in ['original', 'replica', '100% genuine']:
    col = f'keyword_{k.replace(" ", "_")}'
    if col in df.columns:
        feature_cols.append(col)

X = df[feature_cols]
y = df['label'].str.strip().str.lower().map({'genuine': 1, 'fake': 0})

# Check for unmapped labels
if y.isnull().any():
    print("Found unmapped labels:", df['label'][y.isnull()])
    exit(1)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(clf, 'ml/model.pkl')
print('Model saved to ml/model.pkl') 