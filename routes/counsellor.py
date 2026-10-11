from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Student, Counsellor, Observation, RiskAssessment, CounsellingSession, Recommendation
from routes.decorators import role_required
from datetime import datetime

counsellor = Blueprint('counsellor', __name__, url_prefix='/counsellor')

@counsellor.before_request
@login_required
@role_required('counsellor')
def counsellor_protection():
    pass

@counsellor.route('/dashboard')
def dashboard():
    counsellor_profile = Counsellor.query.filter_by(user_id=current_user.id).first()
    
    # Upcoming scheduled sessions
    upcoming_sessions = CounsellingSession.query.filter_by(
        counsellor_id=counsellor_profile.id, 
        status='scheduled'
    ).order_by(CounsellingSession.scheduled_at.asc()).all()
    
    # Completed sessions count
    completed_count = CounsellingSession.query.filter_by(
        counsellor_id=counsellor_profile.id, 
        status='completed'
    ).count()
    
    # All active cases (scheduled sessions)
    active_cases_count = len(upcoming_sessions)
    
    # Get high-risk students for referral queue
    high_risk_students = []
    all_sessions = CounsellingSession.query.filter_by(counsellor_id=counsellor_profile.id).all()
    student_ids = set(s.student_id for s in all_sessions)
    for sid in student_ids:
        latest_risk = RiskAssessment.query.filter_by(student_id=sid).order_by(RiskAssessment.assessed_at.desc()).first()
        if latest_risk and latest_risk.risk_level == 'high':
            student = Student.query.get(sid)
            if student:
                student.latest_risk = latest_risk
                high_risk_students.append(student)
                
    stats = {
        'new_referrals': len(high_risk_students),
        'active_cases': active_cases_count,
        'sessions_week': len(upcoming_sessions),
        'completed': completed_count
    }
    
    formatted_referrals = []
    for s in high_risk_students:
        formatted_referrals.append({
            'name': s.user.name if s.user else f'Student #{s.id}',
            'teacher': s.department or 'Faculty',
            'risk': s.latest_risk.risk_level.capitalize() if s.latest_risk else 'Medium',
            'date': s.latest_risk.assessed_at.strftime('%Y-%m-%d') if s.latest_risk and s.latest_risk.assessed_at else 'Recent'
        })
        
    formatted_sessions = []
    for sess in upcoming_sessions:
        st = sess.student
        formatted_sessions.append({
            'name': st.user.name if (st and st.user) else f'Student #{sess.student_id}',
            'time': sess.scheduled_at.strftime('%b %d, %I:%M %p') if sess.scheduled_at else 'TBD'
        })
    
    return render_template('counsellor/dashboard.html', 
                           counsellor=counsellor_profile,
                           stats=stats,
                           referrals=formatted_referrals,
                           sessions=formatted_sessions,
                           upcoming_sessions=upcoming_sessions,
                           active_cases_count=active_cases_count,
                           completed_count=completed_count,
                           high_risk_students=high_risk_students)

@counsellor.route('/referrals')
def referrals():
    counsellor_profile = Counsellor.query.filter_by(user_id=current_user.id).first()
    # Get all students referred to this counsellor, sorted by risk
    sessions = CounsellingSession.query.filter_by(counsellor_id=counsellor_profile.id).all()
    
    referred_students = []
    seen_ids = set()
    for s in sessions:
        if s.student_id not in seen_ids:
            seen_ids.add(s.student_id)
            student = Student.query.get(s.student_id)
            if student:
                student.latest_risk = RiskAssessment.query.filter_by(student_id=s.student_id).order_by(RiskAssessment.assessed_at.desc()).first()
                student.referral_session = s
                referred_students.append(student)
    
    # Sort by risk score (high first)
    referred_students.sort(key=lambda x: x.latest_risk.risk_score if x.latest_risk else 0, reverse=True)
    
    return render_template('counsellor/referrals.html', referrals=referred_students)

@counsellor.route('/students/<int:id>')
def student_detail(id):
    student = Student.query.get_or_404(id)
    observations = Observation.query.filter_by(student_id=id).order_by(Observation.created_at.desc()).all()
    risk_history = RiskAssessment.query.filter_by(student_id=id).order_by(RiskAssessment.assessed_at.desc()).all()
    recommendations = Recommendation.query.filter_by(student_id=id).order_by(Recommendation.created_at.desc()).all()
    
    counsellor_profile = Counsellor.query.filter_by(user_id=current_user.id).first()
    sessions = CounsellingSession.query.filter_by(
        student_id=id, 
        counsellor_id=counsellor_profile.id
    ).order_by(CounsellingSession.scheduled_at.desc()).all()
    
    return render_template('counsellor/student_detail.html', 
                           student=student,
                           observations=observations,
                           risk_history=risk_history,
                           recommendations=recommendations,
                           sessions=sessions)

@counsellor.route('/students/<int:id>/session', methods=['POST'])
def create_session(id):
    student = Student.query.get_or_404(id)
    counsellor_profile = Counsellor.query.filter_by(user_id=current_user.id).first()
    
    session_date_str = request.form.get('date')
    session_notes = request.form.get('notes', '')
    session_type = request.form.get('session_type', 'individual')
    
    try:
        scheduled_at = datetime.strptime(session_date_str, '%Y-%m-%dT%H:%M')
    except (ValueError, TypeError):
        scheduled_at = datetime.utcnow()
    
    new_session = CounsellingSession(
        student_id=student.id,
        counsellor_id=counsellor_profile.id,
        scheduled_at=scheduled_at,
        notes=session_notes,
        session_type=session_type,
        status='scheduled'
    )
    db.session.add(new_session)
    db.session.commit()
    
    flash('Counselling session scheduled.', 'success')
    return redirect(url_for('counsellor.student_detail', id=student.id))

@counsellor.route('/sessions/<int:id>/update', methods=['POST'])
def update_session(id):
    session = CounsellingSession.query.get_or_404(id)
    session.notes = request.form.get('notes', session.notes)
    session.status = request.form.get('status', session.status)
    session.outcome = request.form.get('outcome', session.outcome)
    
    db.session.commit()
    flash('Session updated successfully.', 'success')
    return redirect(url_for('counsellor.dashboard'))

@counsellor.route('/sessions')
def sessions():
    counsellor_profile = Counsellor.query.filter_by(user_id=current_user.id).first()
    status_filter = request.args.get('status')
    
    query = CounsellingSession.query.filter_by(counsellor_id=counsellor_profile.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    sessions_list = query.order_by(CounsellingSession.scheduled_at.desc()).all()
    return render_template('counsellor/sessions.html', sessions=sessions_list)

@counsellor.route('/students/<int:id>/recommend', methods=['POST'])
def recommend(id):
    student = Student.query.get_or_404(id)
    
    content = request.form.get('content')
    rec_type = request.form.get('type', 'study_plan')
    if content:
        rec = Recommendation(
            student_id=student.id,
            type=rec_type,
            content=content
        )
        db.session.add(rec)
        db.session.commit()
        flash('Recommendation added for student.', 'success')
    else:
        flash('Recommendation content cannot be empty.', 'danger')
        
    return redirect(url_for('counsellor.student_detail', id=student.id))
