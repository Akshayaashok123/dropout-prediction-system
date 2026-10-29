from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Student, Counsellor, Observation, RiskAssessment, CounsellingSession, Recommendation, Attendance, Marks
from routes.decorators import role_required
from ml.predictor import DropoutPredictor
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
    
    # Active scheduled or in_progress sessions for this counsellor
    upcoming_sessions = CounsellingSession.query.filter_by(
        counsellor_id=counsellor_profile.id, 
        status='scheduled'
    ).order_by(CounsellingSession.scheduled_at.asc()).all()
    
    in_progress_sessions = CounsellingSession.query.filter_by(
        counsellor_id=counsellor_profile.id,
        status='in_progress'
    ).all()
    
    completed_count = CounsellingSession.query.filter_by(
        counsellor_id=counsellor_profile.id, 
        status='completed'
    ).count()
    
    # High risk students in institution needing review
    all_students = Student.query.all()
    high_risk_students = [s for s in all_students if s.latest_risk_level.lower() == 'high']
    medium_risk_students = [s for s in all_students if s.latest_risk_level.lower() == 'medium']
    
    stats = {
        'high_risk_count': len(high_risk_students),
        'medium_risk_count': len(medium_risk_students),
        'active_cases': len(upcoming_sessions) + len(in_progress_sessions),
        'completed': completed_count,
        'upcoming_count': len(upcoming_sessions)
    }
    
    # Top urgent action queue students (up to 8)
    action_queue_preview = []
    for s in high_risk_students[:8]:
        action_queue_preview.append({
            'student': s,
            'risk_level': s.latest_risk_level,
            'risk_score': s.latest_risk_score,
            'main_reason': (s.latest_assessment.contributing_factors.split(';')[0] if s.latest_assessment and s.latest_assessment.contributing_factors else 'Attendance & Academic concern'),
            'last_intervention': s.latest_intervention
        })
        
    return render_template('counsellor/dashboard.html', 
                           counsellor=counsellor_profile,
                           stats=stats,
                           upcoming_sessions=upcoming_sessions,
                           action_queue_preview=action_queue_preview)

@counsellor.route('/referrals')
@counsellor.route('/action-queue')
def referrals():
    """Mentor Action Queue: Flagged students requiring faculty/mentor review."""
    counsellor_profile = Counsellor.query.filter_by(user_id=current_user.id).first()
    
    search = request.args.get('search', '').strip().lower()
    department = request.args.get('department', '').strip()
    risk_level = request.args.get('risk_level', '').strip()
    status_filter = request.args.get('status', '').strip()
    sort_by = request.args.get('sort', 'risk_desc').strip()
    
    students = Student.query.all()
    queue = []
    
    for s in students:
        # Check risk level
        r_level = s.latest_risk_level.lower()
        
        # We include students who are high or medium risk, or have an active session
        latest_sess = s.latest_intervention
        has_active_sess = latest_sess and latest_sess.status in ['scheduled', 'in_progress']
        
        # Filter: by default show High and Medium risk cases, or active sessions
        if risk_level:
            if r_level != risk_level.lower():
                continue
        elif r_level not in ['high', 'medium'] and not has_active_sess:
            continue
            
        if department and (s.department or '') != department:
            continue
            
        if status_filter:
            current_status = latest_sess.status if latest_sess else 'none'
            if status_filter == 'none' and latest_sess:
                continue
            elif status_filter != 'none' and (not latest_sess or latest_sess.status != status_filter):
                continue
                
        # Search query
        s_name = (s.name or '').lower()
        s_email = (s.email or '').lower()
        if search and (search not in s_name and search not in s_email and search not in str(s.id)):
            continue
            
        main_factor = 'Academic & Engagement Review'
        if s.latest_assessment and s.latest_assessment.contributing_factors:
            factors_list = [f.strip() for f in s.latest_assessment.contributing_factors.split(';') if f.strip()]
            if factors_list:
                main_factor = factors_list[0]
                
        # Recommended next action
        rec_action = 'Schedule 1-on-1 Mentorship Check-in'
        if s.attendance_pct and s.attendance_pct < 65:
            rec_action = 'Review Attendance Barriers & Commute Hurdles'
        elif s.gpa and s.gpa < 5.0:
            rec_action = 'Assign Subject Remedial Tutoring'
            
        queue.append({
            'student': s,
            'id': s.id,
            'name': s.name,
            'email': s.email,
            'department': s.department or 'General',
            'semester': s.semester or 1,
            'attendance_pct': s.attendance_pct or 0.0,
            'gpa': s.gpa or 0.0,
            'risk_level': s.latest_risk_level,
            'risk_score': s.latest_risk_score,
            'main_reason': main_factor,
            'recommended_action': rec_action,
            'latest_session': latest_sess,
            'followup_status': latest_sess.status if latest_sess else 'No Follow-up Yet',
            'last_contact_date': latest_sess.scheduled_at.strftime('%b %d, %Y') if latest_sess else 'None'
        })
        
    # Sorting
    if sort_by == 'risk_desc':
        queue.sort(key=lambda x: x['risk_score'], reverse=True)
    elif sort_by == 'risk_asc':
        queue.sort(key=lambda x: x['risk_score'])
    elif sort_by == 'att_asc':
        queue.sort(key=lambda x: x['attendance_pct'])
    elif sort_by == 'gpa_asc':
        queue.sort(key=lambda x: x['gpa'])
    elif sort_by == 'name':
        queue.sort(key=lambda x: x['name'].lower())
        
    depts = [d[0] for d in db.session.query(Student.department).distinct().all() if d[0]]
    if not depts:
        depts = ['Computer Science', 'Electronics & Comm.', 'Mechanical', 'Civil', 'Electrical']
        
    return render_template('counsellor/referrals.html', 
                           queue=queue,
                           departments=depts,
                           current_search=search,
                           current_dept=department,
                           current_risk=risk_level,
                           current_status=status_filter,
                           current_sort=sort_by)

@counsellor.route('/sessions')
def sessions():
    """Intervention Tracking Center: Manage all counsellor and mentor interactions."""
    counsellor_profile = Counsellor.query.filter_by(user_id=current_user.id).first()
    
    search = request.args.get('search', '').strip().lower()
    status_filter = request.args.get('status', '').strip()
    support_filter = request.args.get('support_type', '').strip()
    
    query = CounsellingSession.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if support_filter:
        query = query.filter_by(support_type=support_filter)
        
    all_sessions = query.order_by(CounsellingSession.scheduled_at.desc()).all()
    
    filtered_sessions = []
    for sess in all_sessions:
        st = sess.student
        st_name = (st.name or '').lower() if st else ''
        if search and (search not in st_name and search not in str(sess.student_id)):
            continue
        filtered_sessions.append(sess)
        
    support_types = [
        'Academic Mentoring',
        'Attendance Barrier Review',
        'Financial Aid Guidance',
        'Wellness / Stress Support',
        'Study Skills Coaching'
    ]
    
    # Counts for quick filter pills
    counts = {
        'total': CounsellingSession.query.count(),
        'scheduled': CounsellingSession.query.filter_by(status='scheduled').count(),
        'in_progress': CounsellingSession.query.filter_by(status='in_progress').count(),
        'completed': CounsellingSession.query.filter_by(status='completed').count()
    }
    
    return render_template('counsellor/sessions.html', 
                           sessions=filtered_sessions,
                           support_types=support_types,
                           counts=counts,
                           current_search=search,
                           current_status=status_filter,
                           current_support=support_filter)

@counsellor.route('/students/<int:id>')
def student_detail(id):
    student = Student.query.get_or_404(id)
    counsellor_profile = Counsellor.query.filter_by(user_id=current_user.id).first()
    
    observations = Observation.query.filter_by(student_id=id).order_by(Observation.created_at.desc()).all()
    risk_history = RiskAssessment.query.filter_by(student_id=id).order_by(RiskAssessment.assessed_at.desc()).all()
    recommendations = Recommendation.query.filter_by(student_id=id).order_by(Recommendation.created_at.desc()).all()
    sessions_list = CounsellingSession.query.filter_by(student_id=id).order_by(CounsellingSession.scheduled_at.desc()).all()
    attendance_records = Attendance.query.filter_by(student_id=id).order_by(Attendance.date.desc()).all()
    marks_records = Marks.query.filter_by(student_id=id).all()
    
    predictor = DropoutPredictor()
    explanation_data = predictor.predict_risk(student.id)
    
    return render_template('counsellor/student_detail.html', 
                           student=student,
                           observations=observations,
                           risk_history=risk_history,
                           recommendations=recommendations,
                           sessions=sessions_list,
                           attendance_records=attendance_records,
                           marks_records=marks_records,
                           explanation=explanation_data)

@counsellor.route('/students/<int:id>/session', methods=['POST'])
def create_session(id):
    student = Student.query.get_or_404(id)
    counsellor_profile = Counsellor.query.filter_by(user_id=current_user.id).first()
    
    session_date_str = request.form.get('date') or request.form.get('scheduled_at')
    next_followup_str = request.form.get('next_followup_date')
    support_type = request.form.get('support_type', 'Academic Mentoring')
    session_notes = request.form.get('notes', '').strip()
    status = request.form.get('status', 'scheduled')
    outcome = request.form.get('outcome', '').strip()
    
    try:
        scheduled_at = datetime.strptime(session_date_str, '%Y-%m-%dT%H:%M')
    except (ValueError, TypeError):
        try:
            scheduled_at = datetime.strptime(session_date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            scheduled_at = datetime.utcnow()
            
    next_followup = None
    if next_followup_str:
        try:
            next_followup = datetime.strptime(next_followup_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    new_session = CounsellingSession(
        student_id=student.id,
        counsellor_id=counsellor_profile.id if counsellor_profile else None,
        mentor_name=current_user.name,
        support_type=support_type,
        scheduled_at=scheduled_at,
        next_followup_date=next_followup,
        notes=session_notes,
        outcome=outcome,
        session_type='individual',
        status=status
    )
    db.session.add(new_session)
    db.session.commit()
    
    flash(f'Intervention recorded successfully for {student.name}.', 'success')
    return redirect(request.referrer or url_for('counsellor.sessions'))

@counsellor.route('/sessions/<int:id>/update', methods=['POST'])
def update_session(id):
    sess = CounsellingSession.query.get_or_404(id)
    sess.notes = request.form.get('notes', sess.notes).strip()
    sess.status = request.form.get('status', sess.status)
    sess.outcome = request.form.get('outcome', sess.outcome).strip()
    sess.support_type = request.form.get('support_type', sess.support_type)
    
    next_followup_str = request.form.get('next_followup_date')
    if next_followup_str:
        try:
            sess.next_followup_date = datetime.strptime(next_followup_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    elif request.form.get('clear_followup') == '1':
        sess.next_followup_date = None
        
    db.session.commit()
    flash('Intervention record updated successfully.', 'success')
    return redirect(request.referrer or url_for('counsellor.sessions'))

@counsellor.route('/students/<int:id>/recommend', methods=['POST'])
def recommend(id):
    student = Student.query.get_or_404(id)
    content = request.form.get('content', '').strip()
    rec_type = request.form.get('type', 'study_plan')
    if content:
        rec = Recommendation(
            student_id=student.id,
            type=rec_type,
            content=content
        )
        db.session.add(rec)
        db.session.commit()
        flash('Recommendation logged for student.', 'success')
    else:
        flash('Recommendation content cannot be empty.', 'danger')
        
    return redirect(url_for('counsellor.student_detail', id=student.id))
