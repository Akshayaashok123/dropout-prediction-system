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
        attendance_pct = student.attendance_pct if student.attendance_pct is not None else 75.0
        attendance_trend = 0.0
        
        if attendances:
            present = sum(1 for a in attendances if a.status and a.status.lower() == 'present')
            late = sum(1 for a in attendances if a.status and a.status.lower() == 'late')
            attendance_pct = ((present + (0.5 * late)) / len(attendances)) * 100.0
            
            # Simple trend: compare first half to second half
            if len(attendances) >= 4:
                half = len(attendances) // 2
                first_half = sum(1 for a in attendances[:half] if a.status and a.status.lower() == 'present') / half
                second_half = sum(1 for a in attendances[half:] if a.status and a.status.lower() == 'present') / (len(attendances) - half)
                attendance_trend = round(second_half - first_half, 3) # Negative if declining
                
        # 2. Marks features
        marks = Marks.query.filter_by(student_id=student_id).all()
        gpa = student.gpa if student.gpa is not None else 7.0
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
            
            if student.gpa is not None:
                gpa = float(student.gpa)
            elif semester_marks_avg > 0:
                gpa = round(semester_marks_avg / 10.0, 2)
                
            # Count backlogs (e.g., marks < 40 in semester exams)
            backlogs_count = sum(1 for m in marks if m.exam_type == 'semester' and m.score is not None and m.score < 40)
        elif student.gpa is not None:
            gpa = float(student.gpa)
            internal_marks_avg = min(100.0, gpa * 10.0)
            semester_marks_avg = min(100.0, gpa * 10.0)
            assignment_score_avg = min(100.0, gpa * 10.0)
            
        engagement_score = round((attendance_pct * 0.5) + (assignment_score_avg * 0.5), 1)
        
        features = {
            'attendance_pct': round(float(attendance_pct), 2),
            'gpa': round(float(gpa), 2),
            'internal_marks_avg': round(float(internal_marks_avg), 1),
            'semester_marks_avg': round(float(semester_marks_avg), 1),
            'assignment_score_avg': round(float(assignment_score_avg), 1),
            'backlogs_count': int(backlogs_count),
            'attendance_trend': round(float(attendance_trend), 3),
            'marks_trend': round(float(marks_trend), 3),
            'engagement_score': round(float(engagement_score), 1)
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
        Returns risk score (0-100) and structured contributing factors.
        """
        risk_points = 0
        factors = []
        
        if features['attendance_pct'] < 60:
            risk_points += 35
            factors.append({
                'factor': 'Critical Attendance Deficit',
                'detail': f"Attendance is {features['attendance_pct']}%, significantly below 75% requirement.",
                'source': 'Rule-Based Attendance Policy',
                'weight': 35
            })
        elif features['attendance_pct'] < 75:
            risk_points += 20
            factors.append({
                'factor': 'Low Attendance Warning',
                'detail': f"Attendance is {features['attendance_pct']}%, nearing critical cutoff.",
                'source': 'Rule-Based Attendance Policy',
                'weight': 20
            })
            
        if features['gpa'] < 4.0:
            risk_points += 30
            factors.append({
                'factor': 'Academic Performance Concern',
                'detail': f"Cumulative GPA is {features['gpa']}, below minimum academic standing (4.0).",
                'source': 'Rule-Based Grade Threshold',
                'weight': 30
            })
        elif features['gpa'] < 5.5:
            risk_points += 15
            factors.append({
                'factor': 'Moderate Academic Underperformance',
                'detail': f"Cumulative GPA is {features['gpa']}. Needs subject-level reinforcement.",
                'source': 'Rule-Based Grade Threshold',
                'weight': 15
            })
            
        if features['backlogs_count'] > 2:
            risk_points += 20
            factors.append({
                'factor': 'Multiple Course Backlogs',
                'detail': f"Currently carrying {features['backlogs_count']} uncleared semester course(s).",
                'source': 'Rule-Based Backlog Limit',
                'weight': 20
            })
        elif features['backlogs_count'] > 0:
            risk_points += 10
            factors.append({
                'factor': 'Pending Course Backlog',
                'detail': f"Carrying {features['backlogs_count']} uncleared course backlog.",
                'source': 'Rule-Based Backlog Limit',
                'weight': 10
            })
            
        if features['attendance_trend'] < -0.15:
            risk_points += 15
            factors.append({
                'factor': 'Declining Attendance Trajectory',
                'detail': 'Attendance rate dropped markedly between earlier and recent academic sessions.',
                'source': 'Rule-Based Trend Analysis',
                'weight': 15
            })
            
        if features['assignment_score_avg'] < 50:
            risk_points += 10
            factors.append({
                'factor': 'Low Assignment Engagement',
                'detail': f"Assignment submission score average is {features['assignment_score_avg']}%.",
                'source': 'Rule-Based Submission Monitor',
                'weight': 10
            })
            
        risk_score = min(risk_points, 100)
        
        # Sort factors by weight
        factors.sort(key=lambda x: x['weight'], reverse=True)
        top_factors = factors[:4]
        
        if not top_factors:
            top_factors = [{
                'factor': 'Satisfactory Academic Standing',
                'detail': 'Attendance and academic markers are currently within standard ranges.',
                'source': 'Baseline Evaluation',
                'weight': 0
            }]
             
        return risk_score, top_factors

    def predict_risk(self, student_id):
        """
        Extract features, run model or rules, and return explainable risk assessment dict.
        """
        try:
            features = self.extract_features(student_id)
        except ValueError as e:
            return {"error": str(e)}
            
        risk_score = 0
        assessment_source = "Rule-Based Early-Warning Engine"
        
        # Calculate rule factors as foundation for explainability
        rule_score, detailed_factors = self._rule_based_predict(features)
        
        if self.model:
            try:
                # Prepare feature array in correct order
                X = pd.DataFrame([features])[self.features_list]
                prob = self.model.predict_proba(X)[0][1]
                risk_score = int(round(prob * 100))
                assessment_source = "Random Forest Classifier (Supervised ML)"
            except Exception as e:
                print(f"ML prediction failed: {e}. Falling back to rules.")
                risk_score = rule_score
                assessment_source = "Rule-Based Early-Warning Engine"
        else:
            risk_score = rule_score
            assessment_source = "Rule-Based Early-Warning Engine"
            
        # Determine risk priority category
        if risk_score <= 35:
            risk_level = 'low'
        elif risk_score <= 65:
            risk_level = 'medium'
        else:
            risk_level = 'high'
            
        # Pedagogical mentor review reason
        if risk_level == 'high':
            mentor_reason = (
                "Combined indicators (low attendance and/or academic performance) signal significant barrier risk. "
                "Immediate faculty/mentor check-in is recommended to address potential personal, transit, or curriculum roadblocks."
            )
        elif risk_level == 'medium':
            mentor_reason = (
                "Emerging decline in engagement or course scores. Proactive advisory meeting can prevent escalation into critical risk."
            )
        else:
            mentor_reason = (
                "Student is progressing satisfactorily with no immediate intervention indicated. Continue routine milestone tracking."
            )
            
        # Actionable next steps for counsellors
        next_steps = []
        if features['attendance_pct'] < 75:
            next_steps.append("Schedule attendance inquiry to identify transit, health, or family schedule constraints.")
        if features['gpa'] < 5.5 or features['backlogs_count'] > 0:
            next_steps.append("Connect with department tutor for subject-specific remedial sessions and study timetable.")
        if features['assignment_score_avg'] < 60:
            next_steps.append("Review assignment submission deadlines and provide task breakdown assistance.")
        if not next_steps:
            next_steps.append("Acknowledge consistent performance; recommend campus leadership and peer mentoring opportunities.")
            
        factor_summaries = [f"{f['factor']}: {f['detail']}" for f in detailed_factors]
            
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'assessment_source': assessment_source,
            'confidence_disclaimer': 'Early-warning propensity score for human-in-the-loop review. Does not determine eligibility or guarantee dropout.',
            'contributing_factors': factor_summaries,
            'detailed_factors': detailed_factors,
            'mentor_review_reason': mentor_reason,
            'suggested_next_steps': next_steps,
            'features': features,
            'wellness_score': max(0, 100 - risk_score),
            'assessed_at': datetime.utcnow()
        }

    def get_recommendations(self, risk_level, factors):
        """
        Generate personalized recommendations linked to evidence.
        """
        recommendations = []
        factors_text = " ".join(factors).lower()
        
        if risk_level == 'low':
            recommendations.append("Continue current study routines and maintain consistent lecture participation.")
            recommendations.append("Explore extracurricular academic projects or peer tutoring roles.")
        elif risk_level == 'medium':
            if 'attendance' in factors_text:
                recommendations.append("Establish a daily class attendance plan; notify faculty early in case of transit or health delays.")
            if 'gpa' in factors_text or 'backlog' in factors_text or 'academic' in factors_text:
                recommendations.append("Join weekly departmental remedial study groups for challenging core subjects.")
            recommendations.append("Schedule a 15-minute supportive check-in with your assigned faculty advisor.")
        else: # High risk
            recommendations.append("Urgent Priority: Meet with the campus student support counsellor for an individualized assistance plan.")
            if 'attendance' in factors_text:
                recommendations.append("Attendance Barrier Review: Identify external or commute challenges preventing regular class presence.")
            if 'backlog' in factors_text or 'gpa' in factors_text:
                recommendations.append("Enroll in academic recovery coaching and focus on prerequisite conceptual foundations.")
            recommendations.append("Explore institutional scholarship, fee installment, or hardship support options if experiencing financial pressures.")
            
        return recommendations

    def predict_all(self):
        """
        Run prediction for ALL students, save RiskAssessment records to DB.
        """
        db, Student, _, _, RiskAssessment, Recommendation = get_models()
        if not Student or not RiskAssessment:
            return {"error": "Database models not available"}
            
        students = Student.query.all()
        results = {'processed': 0, 'total': len(students), 'low': 0, 'medium': 0, 'high': 0, 'errors': 0}
        
        for student in students:
            try:
                assessment = self.predict_risk(student.id)
                
                # Create new RiskAssessment record
                ra = RiskAssessment(
                    student_id=student.id,
                    risk_score=assessment['risk_score'],
                    risk_level=assessment['risk_level'],
                    contributing_factors="; ".join(assessment['contributing_factors']),
                    assessment_source=assessment['assessment_source'],
                    assessed_at=assessment['assessed_at']
                )
                db.session.add(ra)
                
                # Update student's cached metrics
                feats = assessment.get('features') or self.extract_features(student.id)
                student.attendance_pct = feats['attendance_pct']
                student.gpa = feats['gpa']
                
                # Generate and save recommendations
                recs = self.get_recommendations(assessment['risk_level'], assessment['contributing_factors'])
                
                rec_types = {
                    'attendance': 'attendance_reminder',
                    'remedial': 'study_plan',
                    'study': 'study_plan',
                    'counsellor': 'counsellor_referral',
                    'financial': 'financial_aid',
                    'Continue': 'motivation',
                    'Explore': 'motivation'
                }
                
                for rec_text in recs:
                    rec_type = 'motivation'
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
