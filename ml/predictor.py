import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

# Lazy loading of models to avoid circular imports if imported globally
def get_models():
    try:
        # Assuming app is running and models are importable from root 'models' module
        import sys
        # Make sure the project root is in path if necessary
        # sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from models import db, Student, Marks, Attendance, RiskAssessment, Recommendation
        return db, Student, Marks, Attendance, RiskAssessment, Recommendation
    except ImportError:
        print("Warning: Could not import Flask models. Database operations will fail.")
        return None, None, None, None, None, None

class DropoutPredictor:
    def __init__(self):
        """
        Initialize the predictor.
        Loads the trained model if available, otherwise falls back to rule-based prediction.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(current_dir, 'model.joblib')
        self.features_path = os.path.join(current_dir, 'features.joblib')
        
        self.model = None
        self.features_list = [
            'attendance_pct', 'gpa', 'internal_marks_avg', 'semester_marks_avg',
            'assignment_score_avg', 'backlogs_count', 'attendance_trend',
            'marks_trend', 'engagement_score'
        ]
        
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                if os.path.exists(self.features_path):
                    self.features_list = joblib.load(self.features_path)
                print("ML Model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}. Falling back to rule-based predictor.")
        else:
            print("Model file not found. Using rule-based fallback predictor.")

    def extract_features(self, student_id):
        """
        Query DB for a student's data, compute all features, return as dict.
        """
        db, Student, Marks, Attendance, _, _ = get_models()
        if not Student:
            # Return dummy data if DB not available (for testing)
            return self._get_dummy_features()
            
        student = Student.query.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")
            
        # 1. Attendance features
        attendances = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.asc()).all()
        attendance_pct = 75.0 # Default
        attendance_trend = 0.0
        
        if attendances:
            present = sum(1 for a in attendances if a.status == 'Present')
            attendance_pct = (present / len(attendances)) * 100
            
            # Simple trend: compare first half to second half
            if len(attendances) >= 4:
                half = len(attendances) // 2
                first_half = sum(1 for a in attendances[:half] if a.status == 'Present') / half
                second_half = sum(1 for a in attendances[half:] if a.status == 'Present') / (len(attendances) - half)
                attendance_trend = second_half - first_half # Negative if declining
                
        # 2. Marks features
        marks = Marks.query.filter_by(student_id=student_id).all()
        gpa = 7.0 # Default
        internal_marks_avg = 70.0
        semester_marks_avg = 70.0
        assignment_score_avg = 70.0
        backlogs_count = 0
        marks_trend = 0.0
        
        if marks:
            internal_marks = [m.score for m in marks if m.exam_type == 'internal' and m.score is not None]
            semester_marks = [m.score for m in marks if m.exam_type == 'semester' and m.score is not None]
            assignment_marks = [m.score for m in marks if m.exam_type == 'assignment' and m.score is not None]
            
            if internal_marks: internal_marks_avg = sum(internal_marks) / len(internal_marks)
            if semester_marks: semester_marks_avg = sum(semester_marks) / len(semester_marks)
            if assignment_marks: assignment_score_avg = sum(assignment_marks) / len(assignment_marks)
            
            # Estimate GPA from semester marks (assuming max 100 -> 10.0 GPA)
            if semester_marks_avg > 0:
                gpa = semester_marks_avg / 10.0
                
            # Count backlogs (e.g., marks < 40 in semester exams)
            backlogs_count = sum(1 for m in marks if m.exam_type == 'semester' and m.score is not None and m.score < 40)
            
        engagement_score = (attendance_pct * 0.5) + (assignment_score_avg * 0.5)
        
        features = {
            'attendance_pct': attendance_pct,
            'gpa': gpa,
            'internal_marks_avg': internal_marks_avg,
            'semester_marks_avg': semester_marks_avg,
            'assignment_score_avg': assignment_score_avg,
            'backlogs_count': backlogs_count,
            'attendance_trend': attendance_trend,
            'marks_trend': marks_trend,
            'engagement_score': engagement_score
        }
        
        return features
        
    def _get_dummy_features(self):
        """Return dummy features for testing when DB is unavailable"""
        return {
            'attendance_pct': 65.0,
            'gpa': 5.5,
            'internal_marks_avg': 60.0,
            'semester_marks_avg': 55.0,
            'assignment_score_avg': 70.0,
            'backlogs_count': 1,
            'attendance_trend': -0.1,
            'marks_trend': 0.0,
            'engagement_score': 67.5
        }

    def _rule_based_predict(self, features):
        """
        Fallback prediction using weighted rules (no ML model needed).
        Returns risk score (0-100) and contributing factors.
        """
        risk_points = 0
        factors = []
        
        if features['attendance_pct'] < 60:
            risk_points += 30
            factors.append(('Low attendance', 30))
            
        if features['gpa'] < 4.0:
            risk_points += 25
            factors.append(('Low GPA', 25))
            
        if features['backlogs_count'] > 2:
            risk_points += 20
            factors.append(('High backlogs', 20))
            
        if features['attendance_trend'] < -0.2: # Threshold for declining
            risk_points += 15
            factors.append(('Declining attendance', 15))
            
        if features['assignment_score_avg'] < 50:
            risk_points += 10
            factors.append(('Poor assignment performance', 10))
            
        # Ensure max 100
        risk_score = min(risk_points, 100)
        
        # Get top 3 factors
        factors.sort(key=lambda x: x[1], reverse=True)
        top_factors = [f[0] for f in factors[:3]]
        
        if not top_factors and risk_score == 0:
             top_factors = ["Consistent academic performance"]
             
        return risk_score, top_factors

    def predict_risk(self, student_id):
        """
        Extract features, run model or rules, return risk assessment dict.
        """
        try:
            features = self.extract_features(student_id)
        except ValueError as e:
            return {"error": str(e)}
            
        factors = []
        risk_score = 0
        
        if self.model:
            # Prepare feature array in correct order
            X = pd.DataFrame([features])[self.features_list]
            
            # Predict probability of dropout (class 1)
            # RandomForest predict_proba returns array of [prob_class_0, prob_class_1]
            try:
                prob = self.model.predict_proba(X)[0][1]
                risk_score = int(prob * 100)
                
                # Derive factors heuristically for ML since RF doesn't give instance-level feature importance easily without SHAP
                _, rule_factors = self._rule_based_predict(features)
                factors = rule_factors
                
            except Exception as e:
                print(f"ML prediction failed: {e}. Falling back to rules.")
                risk_score, factors = self._rule_based_predict(features)
        else:
            # Rule based fallback
            risk_score, factors = self._rule_based_predict(features)
            
        # Determine risk level
        if risk_score <= 30:
            risk_level = 'low'
        elif risk_score <= 60:
            risk_level = 'medium'
        else:
            risk_level = 'high'
            
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'contributing_factors': factors,
            'wellness_score': 100 - risk_score # For non-stigmatizing UI
        }

    def get_recommendations(self, risk_level, factors):
        """
        Generate personalized recommendations based on risk level and factors.
        """
        recommendations = []
        
        if risk_level == 'low':
            recommendations.append("Keep up the good work! Maintain your current study habits.")
            recommendations.append("Consider joining advanced study groups or technical clubs.")
            
        elif risk_level == 'medium':
            if 'Low attendance' in factors or 'Declining attendance' in factors:
                recommendations.append("Set a daily reminder for classes and aim to improve attendance to >75%.")
            if 'Low GPA' in factors or 'High backlogs' in factors:
                recommendations.append("Create a structured weekly study plan focusing on weaker subjects.")
            recommendations.append("Schedule a brief check-in with your academic advisor.")
            
        else: # High risk
            recommendations.append("Schedule an immediate appointment with the student counsellor.")
            if 'High backlogs' in factors:
                recommendations.append("Attend remedial classes and peer tutoring sessions for backlog subjects.")
            if 'Low attendance' in factors:
                recommendations.append("Urgent: Discuss attendance issues with your mentor to find solutions.")
            recommendations.append("Break down assignments into smaller, manageable daily tasks.")
            
        return recommendations

    def predict_all(self):
        """
        Run prediction for ALL students, save RiskAssessment records to DB.
        """
        db, Student, _, _, RiskAssessment, Recommendation = get_models()
        if not Student or not RiskAssessment:
            return {"error": "Database models not available"}
            
        students = Student.query.all()
        results = {'processed': 0, 'total': 0, 'low': 0, 'medium': 0, 'high': 0, 'errors': 0}
        results['total'] = len(students)
        
        for student in students:
            try:
                assessment = self.predict_risk(student.id)
                
                # Create new RiskAssessment record (keep history)
                ra = RiskAssessment(
                    student_id=student.id,
                    risk_score=assessment['risk_score'],
                    risk_level=assessment['risk_level'],
                    contributing_factors=", ".join(assessment['contributing_factors']),
                    assessed_at=datetime.utcnow()
                )
                db.session.add(ra)
                
                # Update student's cached attendance_pct and gpa
                features = self.extract_features(student.id)
                student.attendance_pct = features['attendance_pct']
                student.gpa = features['gpa']
                
                # Generate and save recommendations
                recs = self.get_recommendations(assessment['risk_level'], assessment['contributing_factors'])
                
                # Determine recommendation types based on content
                rec_types = {
                    'attendance': 'attendance_reminder',
                    'study': 'study_plan',
                    'counsellor': 'counsellor_referral',
                    'Keep up': 'motivation',
                    'Consider': 'motivation',
                    'remedial': 'study_plan',
                    'Break down': 'study_plan',
                }
                
                for rec_text in recs:
                    rec_type = 'motivation'  # default
                    for keyword, rtype in rec_types.items():
                        if keyword.lower() in rec_text.lower():
                            rec_type = rtype
                            break
                    
                    rec = Recommendation(
                        student_id=student.id,
                        type=rec_type,
                        content=rec_text
                    )
                    db.session.add(rec)
                    
                # Update stats
                results['processed'] += 1
                results[assessment['risk_level']] += 1
                
            except Exception as e:
                print(f"Error processing student {student.id}: {e}")
                results['errors'] += 1
                
        try:
            db.session.commit()
            return results
        except Exception as e:
            db.session.rollback()
            return {"error": f"Database commit failed: {e}"}

# For testing independently
if __name__ == "__main__":
    predictor = DropoutPredictor()
    # Test rule-based
    test_features = predictor._get_dummy_features()
    print("Test features:", test_features)
    print("Rule-based prediction:", predictor._rule_based_predict(test_features))
