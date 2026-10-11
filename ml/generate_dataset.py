import pandas as pd
import numpy as np
import os

def generate_dataset(num_samples=1000, output_path='student_dataset.csv'):
    """
    Generate a synthetic dataset of student records for training the dropout prediction model.
    Realistic distributions and correlations are built in.
    """
    np.random.seed(42)
    
    # 1. Attendance % (Normal dist, truncated to 0-100)
    attendance_pct = np.clip(np.random.normal(75, 15, num_samples), 0, 100)
    
    # 2. GPA (0-10) - Correlated with attendance
    gpa_base = (attendance_pct / 100) * 8 + np.random.normal(0, 1, num_samples)
    gpa = np.clip(gpa_base, 0, 10)
    
    # 3. Internal marks avg (0-100) - Correlated with GPA
    internal_marks_avg = np.clip(gpa * 10 + np.random.normal(0, 5, num_samples), 0, 100)
    
    # 4. Semester marks avg (0-100) - Correlated with GPA
    semester_marks_avg = np.clip(gpa * 9 + np.random.normal(0, 7, num_samples), 0, 100)
    
    # 5. Assignment score avg (0-100) - Correlated with attendance
    assignment_score_avg = np.clip(attendance_pct * 0.9 + np.random.normal(5, 10, num_samples), 0, 100)
    
    # 6. Backlogs count - Inversely correlated with GPA
    backlog_prob = np.clip((10 - gpa) / 10, 0, 1)
    backlogs_count = np.random.binomial(n=6, p=backlog_prob)
    
    # 7. Attendance trend (-1 to 1) - Negative means declining
    attendance_trend = np.clip(np.random.normal((attendance_pct - 50) / 100, 0.3, num_samples), -1, 1)
    
    # 8. Marks trend (-1 to 1)
    marks_trend = np.clip(np.random.normal((gpa - 5) / 10, 0.3, num_samples), -1, 1)
    
    # 9. Engagement score (0-100)
    engagement_score = np.clip(attendance_pct * 0.5 + assignment_score_avg * 0.5 + np.random.normal(0, 10, num_samples), 0, 100)
    
    # Create DataFrame
    df = pd.DataFrame({
        'student_id': range(1, num_samples + 1),
        'attendance_pct': attendance_pct,
        'gpa': gpa,
        'internal_marks_avg': internal_marks_avg,
        'semester_marks_avg': semester_marks_avg,
        'assignment_score_avg': assignment_score_avg,
        'backlogs_count': backlogs_count,
        'attendance_trend': attendance_trend,
        'marks_trend': marks_trend,
        'engagement_score': engagement_score
    })
    
    # Calculate target (dropped_out) based on rules + noise
    # Base risk score calculation
    risk_score = np.zeros(num_samples)
    
    # Apply rules
    risk_score += np.where(attendance_pct < 60, 30, 0)
    risk_score += np.where(gpa < 4.0, 25, 0)
    risk_score += np.where(backlogs_count > 2, 20, 0)
    risk_score += np.where(attendance_trend < -0.3, 15, 0)
    risk_score += np.where(assignment_score_avg < 50, 10, 0)
    
    # Map to probability (logistic function with noise)
    risk_prob = 1 / (1 + np.exp(-(risk_score - 50) / 15)) # Shift and scale
    
    # Add noise to prob
    noise = np.random.uniform(-0.1, 0.1, num_samples)
    risk_prob = np.clip(risk_prob + noise, 0, 1)
    
    # Generate binary outcome
    dropped_out = np.random.binomial(n=1, p=risk_prob)
    df['dropped_out'] = dropped_out
    
    # Save to CSV
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"Generated {num_samples} records and saved to {output_path}")
    print("\nDataset Statistics:")
    print("-" * 50)
    print(df.describe())
    print("\nDropout Distribution:")
    print(df['dropped_out'].value_counts(normalize=True))
    
    return df

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, 'student_dataset.csv')
    generate_dataset(output_path=output_file)
