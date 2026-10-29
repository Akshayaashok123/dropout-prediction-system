from datetime import datetime, date
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Student, Teacher, Observation, Notification, RiskAssessment, Attendance, Marks
from routes.decorators import role_required

teacher = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher.before_request
@login_required
@role_required('teacher')
def teacher_protection():
    pass

@teacher.route('/dashboard')
def dashboard():
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    department = teacher_profile.department if teacher_profile else 'General'
    
    # Get students in teacher's department
    students = Student.query.filter_by(department=department).all()
    
    # Get risk stats for department students
    student_ids = [s.id for s in students]
    high_risk = 0
    medium_risk = 0
    low_risk = 0
    for s in students:
        latest = RiskAssessment.query.filter_by(student_id=s.id).order_by(RiskAssessment.assessed_at.desc()).first()
        if latest:
            if latest.risk_level == 'high':
                high_risk += 1
            elif latest.risk_level == 'medium':
                medium_risk += 1
            else:
                low_risk += 1
    
    # Recent notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    
    stats = {
        'total': len(students),
        'at_risk': high_risk,
        'needs_attention': medium_risk,
        'stable': low_risk
    }
    
    top_risk_students = []
    sorted_students = sorted(students, key=lambda x: x.latest_risk_score, reverse=True)[:5]
    for s in sorted_students:
        top_risk_students.append({
            'id': s.id,
            'name': s.name,
            'score': s.latest_risk_score,
            'risk': s.latest_risk_level
        })
    
    return render_template('teacher/dashboard.html', 
                           teacher=teacher_profile,
                           students=students,
                           department=department,
                           stats=stats,
                           top_risk_students=top_risk_students,
                           high_risk=high_risk,
                           medium_risk=medium_risk,
                           low_risk=low_risk,
                           notifications=notifications)

@teacher.route('/students')
def students():
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    department = teacher_profile.department if teacher_profile else None
    
    students_list = Student.query.filter_by(department=department).all()
    
    # Attach latest risk assessment to each student
    for s in students_list:
        s.latest_risk = RiskAssessment.query.filter_by(student_id=s.id).order_by(RiskAssessment.assessed_at.desc()).first()
    
    return render_template('teacher/students.html', students=students_list)

@teacher.route('/students/<int:id>')
def student_detail(id):
    student = Student.query.get_or_404(id)
    # Fetch related data for graphs/charts
    attendance = Attendance.query.filter_by(student_id=id).order_by(Attendance.date.desc()).all()
    marks = Marks.query.filter_by(student_id=id).all()
    risk_history = RiskAssessment.query.filter_by(student_id=id).order_by(RiskAssessment.assessed_at.desc()).all()
    observations = Observation.query.filter_by(student_id=id).order_by(Observation.created_at.desc()).all()
    
    latest_ra = RiskAssessment.query.filter_by(student_id=id).order_by(RiskAssessment.assessed_at.desc()).first()
    
    # Structure risk factors for explainability (like SHAP insights)
    factors_list = []
    if latest_ra and latest_ra.contributing_factors:
        # Split by comma if stored as comma-separated or dict string
        raw_factors = [f.strip() for f in latest_ra.contributing_factors.replace('{','').replace('}','').replace('"','').split(',') if f.strip()]
        for f in raw_factors:
            factors_list.append(f.replace(':', ' - ').capitalize())
    
    if not factors_list:
        if student.attendance_pct and student.attendance_pct < 70:
            factors_list.append("Low lecture attendance (<70%)")
        if student.gpa and student.gpa < 5.0:
            factors_list.append("Semester GPA below academic threshold")
        factors_list.append("Irregular assignment submissions")

    # Format observations for template
    formatted_obs = []
    for o in observations:
        formatted_obs.append({
            'date': o.created_at.strftime('%b %d, %Y') if o.created_at else 'Recent',
            'category': o.category or 'Observation',
            'text': o.content
        })

    student.name = student.user.name if student.user else f'Student #{student.id}'
    student.email = student.user.email if student.user else ''
    student.risk_level = (latest_ra.risk_level.capitalize() if latest_ra else 'Low')
    student.risk_score = round(latest_ra.risk_score, 1) if latest_ra else 15

    # Compute real attendance trend (4 weekly blocks)
    today = date.today()
    week_counts = {1: {'present': 0.0, 'total': 0}, 2: {'present': 0.0, 'total': 0}, 3: {'present': 0.0, 'total': 0}, 4: {'present': 0.0, 'total': 0}}
    for a in attendance:
        days_ago = (today - a.date).days if a.date else 0
        w_idx = min(4, max(1, (days_ago // 7) + 1))
        week_counts[w_idx]['total'] += 1
        st = (a.status or '').lower()
        if st == 'present':
            week_counts[w_idx]['present'] += 1.0
        elif st == 'late':
            week_counts[w_idx]['present'] += 0.5
            
    att_labels = ['Week 4 (Past)', 'Week 3', 'Week 2', 'Week 1 (Recent)']
    att_data = []
    base_att = float(student.attendance_pct or 75.0)
    for w in [4, 3, 2, 1]:
        tot = week_counts[w]['total']
        pct = round((week_counts[w]['present'] / tot) * 100, 1) if tot > 0 else base_att
        att_data.append(pct)

    # Compute real marks by subject (prefer semester exams)
    sub_scores = {}
    for m in marks:
        if m.subject:
            if m.subject not in sub_scores or m.exam_type == 'semester':
                sub_scores[m.subject] = round(float(m.score or 0), 1)
    
    marks_labels = list(sub_scores.keys())
    marks_data = [sub_scores[k] for k in marks_labels]
    if not marks_labels:
        marks_labels = ['Academic Progress']
        marks_data = [round(float(student.gpa or 7.0) * 10, 1)]

    return render_template('teacher/student_detail.html', 
                           student=student,
                           factors=factors_list,
                           attendance=attendance,
                           marks=marks,
                           risk_history=risk_history,
                           observations=formatted_obs,
                           att_labels=att_labels,
                           att_data=att_data,
                           marks_labels=marks_labels,
                           marks_data=marks_data)

@teacher.route('/students/<int:id>/observe', methods=['POST'])
def observe(id):
    student = Student.query.get_or_404(id)
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    content = request.form.get('content')
    category = request.form.get('category', 'academic')
    if content:
        observation = Observation(
            student_id=student.id,
            teacher_id=teacher_profile.id,
            content=content,
            category=category
        )
        db.session.add(observation)
        db.session.commit()
        flash('Observation logged successfully.', 'success')
    else:
        flash('Observation content cannot be empty.', 'danger')
        
    return redirect(url_for('teacher.student_detail', id=student.id))

@teacher.route('/students/<int:id>/refer', methods=['POST'])
def refer(id):
    from models import CounsellingSession, Counsellor
    student = Student.query.get_or_404(id)
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    reason = request.form.get('reason', '')
    
    # Find an available counsellor
    counsellor = Counsellor.query.first()
    if counsellor:
        from datetime import datetime
        session = CounsellingSession(
            student_id=student.id,
            counsellor_id=counsellor.id,
            scheduled_at=datetime.utcnow(),
            status='scheduled',
            session_type='individual',
            notes=f'Referred by {current_user.name}. Reason: {reason}'
        )
        db.session.add(session)
        
        # Notify the counsellor
        notification = Notification(
            user_id=counsellor.user_id,
            title='New Student Referral',
            message=f'{student.user.name} has been referred by {current_user.name}. Reason: {reason}',
            type='alert'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f'Student {student.user.name} has been referred to a counsellor.', 'success')
    else:
        flash('No counsellors available at this time.', 'warning')
    
    return redirect(url_for('teacher.student_detail', id=student.id))

@teacher.route('/alerts')
def alerts():
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    department = teacher_profile.department if teacher_profile else 'General'
    
    # Notifications
    alerts_list = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Also fetch department students requiring review
    dept_students = Student.query.filter_by(department=department).all()
    flagged_students = []
    for s in dept_students:
        if s.latest_risk_level.lower() in ['high', 'medium'] or (s.attendance_pct and s.attendance_pct < 75):
            flagged_students.append(s)
            
    flagged_students.sort(key=lambda x: x.latest_risk_score, reverse=True)
    
    return render_template('teacher/alerts.html', 
                           alerts=alerts_list, 
                           flagged_students=flagged_students, 
                           department=department)
