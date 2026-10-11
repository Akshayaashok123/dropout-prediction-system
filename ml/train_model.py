import pandas as pd
import numpy as np
import sys
import os
# Add parent directory to path so we can run from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_dataset import generate_dataset
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

def train_and_save_model():
    """
    Train a Random Forest model on synthetic student data and save it.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, 'student_dataset.csv')
    model_path = os.path.join(current_dir, 'model.joblib')
    
    # Check if dataset exists, if not generate it
    if not os.path.exists(dataset_path):
        print("Dataset not found. Generating...")
        df = generate_dataset(1000, dataset_path)
    else:
        print(f"Loading dataset from {dataset_path}...")
        df = pd.read_csv(dataset_path)
        
    features = [
        'attendance_pct', 'gpa', 'internal_marks_avg', 'semester_marks_avg',
        'assignment_score_avg', 'backlogs_count', 'attendance_trend',
        'marks_trend', 'engagement_score'
    ]
    target = 'dropped_out'
    
    X = df[features]
    y = df[target]
    
    # Train/test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train Random Forest
    print("\nTraining Random Forest classifier...")
    # Use probability estimates, so train a classifier
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate
    print("\nEvaluating model...")
    y_pred = clf.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    
    # Feature importances
    importances = clf.feature_importances_
    feature_importances = pd.DataFrame({'feature': features, 'importance': importances})
    feature_importances = feature_importances.sort_values('importance', ascending=False)
    print("\nFeature Importances:")
    print(feature_importances)
    
    # Save model
    joblib.dump(clf, model_path)
    print(f"\nModel saved successfully to {model_path}")
    
    # Also save the feature list to ensure consistency during inference
    joblib.dump(features, os.path.join(current_dir, 'features.joblib'))

if __name__ == "__main__":
    train_and_save_model()
