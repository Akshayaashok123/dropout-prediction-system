from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from models import db, User, Student, Teacher, Counsellor, RiskAssessment
from routes.decorators import role_required
import csv
import io

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.before_request
@login_required
@role_required('admin')
def admin_protection():
    pass # All routes in this blueprint require admin role

@admin.route('/dashboard')
def dashboard():
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_counsellors = Counsellor.query.count()
    
    # Query latest assessments for counts
    high_risk_count = RiskAssessment.query.filter(RiskAssessment.risk_level.ilike('high')).count()
    medium_risk_count = RiskAssessment.query.filter(RiskAssessment.risk_level.ilike('medium')).count()
    low_risk_count = RiskAssessment.query.filter(RiskAssessment.risk_level.ilike('low')).count()
    
    stats = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_counsellors': total_counsellors,
        'high_risk': high_risk_count,
        'medium_risk': medium_risk_count,
        'low_risk': low_risk_count
    }
    
    raw_recent = RiskAssessment.query.order_by(RiskAssessment.assessed_at.desc()).limit(10).all()
    recent_assessments = []
    for a in raw_recent:
        student_obj = a.student
        recent_assessments.append({
            'student_name': student_obj.user.name if (student_obj and student_obj.user) else f'Student #{a.student_id}',
            'department': student_obj.department if student_obj else 'N/A',
            'risk_score': round(a.risk_score, 1) if a.risk_score is not None else 0,
            'level': a.risk_level.capitalize() if a.risk_level else 'Low',
            'date': a.assessed_at.strftime('%Y-%m-%d') if a.assessed_at else ''
        })
    
    return render_template('admin/dashboard.html', 
                           stats=stats,
                           total_students=total_students,
                           total_teachers=total_teachers,
                           total_counsellors=total_counsellors,
                           high_risk_count=high_risk_count,
                           medium_risk_count=medium_risk_count,
                           low_risk_count=low_risk_count,
                           recent_assessments=recent_assessments)

@admin.route('/students')
def students():
    department = request.args.get('department')
    risk_level = request.args.get('risk_level')
    
    query = Student.query
    if department:
        query = query.filter_by(department=department)
        
    students_list = query.all()
    # Filter by risk_level logic would require joining RiskAssessment based on latest
    
    return render_template('admin/students.html', students=students_list)

@admin.route('/students/<int:id>')
def student_detail(id):
    student = Student.query.get_or_404(id)
    return render_template('admin/student_detail.html', student=student)

@admin.route('/students/upload-csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('admin.students'))
        
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('admin.students'))
        
    if file and file.filename.endswith('.csv'):
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        # Process CSV data (mock implementation)
        count = 0
        for row in csv_input:
            # Expected headers: email, name, department, year
            pass 
        
        flash(f'Successfully imported {count} students.', 'success')
    else:
        flash('Please upload a valid CSV file.', 'danger')
        
    return redirect(url_for('admin.students'))

@admin.route('/users')
def users():
    users_list = User.query.all()
    return render_template('admin/users.html', users=users_list)

@admin.route('/analytics')
def analytics():
    # Pass JSON serializable data for charts
    chart_data = {
        'risk_distribution': {'Low': 50, 'Medium': 30, 'High': 20}
    }
    return render_template('admin/analytics.html', chart_data=chart_data)

@admin.route('/run-prediction', methods=['POST'])
def run_prediction():
    """Trigger ML prediction for all students."""
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        from ml.predictor import DropoutPredictor
        predictor = DropoutPredictor()
        results = predictor.predict_all()
        flash(f'Risk prediction completed successfully! {results.get("total", 0)} students assessed.', 'success')
    except Exception as e:
        flash(f'Prediction failed: {str(e)}', 'danger')
    return redirect(url_for('admin.dashboard'))
