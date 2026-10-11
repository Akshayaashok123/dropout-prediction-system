from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Student, Recommendation, CounsellingSession, RiskAssessment, Attendance, Marks, Counsellor
from routes.decorators import role_required
from datetime import datetime

student = Blueprint('student', __name__, url_prefix='/student')

@student.before_request
@login_required
@role_required('student')
def student_protection():
    pass

@student.route('/dashboard')
def dashboard():
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Calculate non-stigmatizing wellness score (inverse of risk)
    latest_assessment = RiskAssessment.query.filter_by(
        student_id=student_profile.id
    ).order_by(RiskAssessment.assessed_at.desc()).first()
    
    if latest_assessment:
        # Wellness = 100 - risk_score (so high risk = low wellness)
        wellness_score = max(0, round(100 - latest_assessment.risk_score))
        risk_level = latest_assessment.risk_level
    else:
        wellness_score = 85  # Default if no assessment yet
        risk_level = 'low'
    
    # Get actual attendance percentage from student profile
    attendance_pct = student_profile.attendance_pct or 0
    gpa = student_profile.gpa or 0
    
    # Upcoming counselling sessions
    upcoming_sessions = CounsellingSession.query.filter_by(
        student_id=student_profile.id, 
        status='scheduled'
    ).order_by(CounsellingSession.scheduled_at.asc()).all()
    
    # Recent recommendations
    recent_recs = Recommendation.query.filter_by(
        student_id=student_profile.id
    ).order_by(Recommendation.created_at.desc()).limit(3).all()
    
    formatted_recs = []
    for r in recent_recs:
        formatted_recs.append({
            'type': r.type,
            'content': r.content,
            'date': r.created_at.strftime('%b %d, %Y') if r.created_at else 'Recent'
        })
        
    # Provide student fields expected by the template
    student_profile.risk_score = latest_assessment.risk_score if latest_assessment else 15
    student_profile.attendance = round(attendance_pct, 1)
    
    return render_template('student/dashboard.html', 
                           student=student_profile,
                           wellness_score=wellness_score,
                           risk_level=risk_level,
                           attendance_pct=round(attendance_pct, 1),
                           gpa=round(gpa, 1),
                           upcoming_sessions=upcoming_sessions,
                           recommendations=formatted_recs,
                           recent_recs=recent_recs)

@student.route('/recommendations')
def recommendations():
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    recs = Recommendation.query.filter_by(
        student_id=student_profile.id
    ).order_by(Recommendation.created_at.desc()).all()
    return render_template('student/recommendations.html', recommendations=recs)

@student.route('/recommendations/<int:id>/acknowledge', methods=['POST'])
def acknowledge_recommendation(id):
    rec = Recommendation.query.get_or_404(id)
    # Make sure this recommendation belongs to the current student
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    if rec.student_id != student_profile.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('student.recommendations'))
        
    rec.acknowledged = True
    rec.acknowledged_at = datetime.utcnow()
    db.session.commit()
    flash('Recommendation acknowledged.', 'success')
    return redirect(url_for('student.recommendations'))

@student.route('/resources')
def resources():
    # Curated helpful resources for students
    resources_list = [
        {
            'category': 'Study Tips',
            'items': [
                {'title': 'Time Management Guide', 'description': 'Learn effective techniques to manage your study schedule and balance coursework.', 'icon': '📘'},
                {'title': 'Active Learning Strategies', 'description': 'Techniques like spaced repetition and active recall to improve retention.', 'icon': '🧠'},
                {'title': 'Exam Preparation Tips', 'description': 'Structured approach to preparing for internal and semester exams.', 'icon': '📝'},
            ]
        },
        {
            'category': 'Mental Health',
            'items': [
                {'title': 'Campus Counselling Centre', 'description': 'Free, confidential counselling services available on campus.', 'icon': '💚'},
                {'title': 'Stress Management', 'description': 'Practical tips for managing academic stress and anxiety.', 'icon': '🧘'},
                {'title': 'Crisis Helpline', 'description': 'iCall: 9152987821 | Vandrevala Foundation: 1860-2662-345', 'icon': '📞'},
            ]
        },
        {
            'category': 'Financial Aid',
            'items': [
                {'title': 'Scholarship Information', 'description': 'Government and institutional scholarships you may be eligible for.', 'icon': '💰'},
                {'title': 'Fee Assistance Program', 'description': 'Apply for fee waivers or instalment plans through the admin office.', 'icon': '📋'},
            ]
        },
        {
            'category': 'Career Guidance',
            'items': [
                {'title': 'Career Counselling', 'description': 'Book a session with the placement cell for career guidance.', 'icon': '🎯'},
                {'title': 'Skill Development', 'description': 'Free online courses and certifications to enhance your skills.', 'icon': '💡'},
            ]
        }
    ]
    return render_template('student/resources.html', resources=resources_list)

@student.route('/request-help', methods=['GET', 'POST'])
def request_help():
    if request.method == 'POST':
        student_profile = Student.query.filter_by(user_id=current_user.id).first()
        category = request.form.get('category', 'Other')
        message = request.form.get('message', '')
        anonymous = request.form.get('anonymous') == 'on'
        
        # Find an available counsellor
        counsellor = Counsellor.query.first()
        if counsellor:
            session = CounsellingSession(
                student_id=student_profile.id,
                counsellor_id=counsellor.id,
                scheduled_at=datetime.utcnow(),
                status='scheduled',
                session_type='individual',
                notes=f'Help Request ({category}): {message}' + (' [Anonymous]' if anonymous else '')
            )
            db.session.add(session)
            db.session.commit()
            
            flash("Your request for help has been submitted. A counsellor will reach out soon. It's okay to ask for help! 💚", 'success')
        else:
            flash('No counsellors available at this time. Please try again later.', 'warning')
        
        return redirect(url_for('student.dashboard'))
    
    return render_template('student/request_help.html')

@student.route('/sessions')
def sessions():
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    sessions_list = CounsellingSession.query.filter_by(
        student_id=student_profile.id
    ).order_by(CounsellingSession.scheduled_at.desc()).all()
    return render_template('student/sessions.html', sessions=sessions_list)

@student.route('/chatbot')
def chatbot():
    return render_template('student/chatbot.html')

@student.route('/chatbot-api', methods=['POST'])
def chatbot_api():
    data = request.get_json() or {}
    user_msg = (data.get('message') or '').lower().strip()
    
    # Intelligent academic counselling response matching
    if any(k in user_msg for k in ['attendance', 'bunk', 'missed classes', 'low attendance']):
        reply = "Falling below 75% attendance triggers automatic alerts. We recommend creating an attendance tracker: set reminders 15 minutes before morning lectures, pair up with a classmate for accountability, and speak to your department mentor early if health or transit issues are getting in the way."
    elif any(k in user_msg for k in ['stress', 'anxiety', 'overwhelmed', 'depressed', 'nervous', 'scared', 'panic']):
        reply = "Academic pressure can definitely feel overwhelming, and recognizing it is an important first step. Try breaking large study chunks into 25-minute Pomodoro sessions with short walks. Most importantly, our campus counsellors are here with confidential, zero-judgment support whenever you need to talk."
    elif any(k in user_msg for k in ['backlog', 'fail', 'failed', 'arrear', 'supply', 'repeat']):
        reply = "Having backlogs is a challenge, but thousands of students clear them every term. Focus first on the prerequisite subjects, solve the previous 3 years' university question papers, and attend department remedial coaching hours. You can also request a peer tutor through EduGuard."
    elif any(k in user_msg for k in ['study plan', 'routine', 'timetable', 'schedule', 'focus']):
        reply = "A high-yield study routine: 1) Tackle your hardest subject during your peak focus window (usually 9 AM - 12 PM), 2) Focus on conceptual summaries rather than passive reading, and 3) Dedicate Friday evenings strictly to practice problem sets."
    elif any(k in user_msg for k in ['money', 'fee', 'financial', 'scholarship', 'funds']):
        reply = "Financial worries should not stop you from learning. The student affairs office offers merit-cum-means assistance, institutional fee instalment options, and state scholarship guidance. Check our 'Resources' tab for links to apply."
    elif any(k in user_msg for k in ['human', 'real person', 'counselor', 'counsellor', 'teacher', 'appointment']):
        reply = "You can schedule a one-on-one session with a qualified counselor immediately. Head over to the 'Get Help' tab or click the button at the top of this chat to request an appointment."
    else:
        reply = "Thank you for reaching out. I'm here to support your learning journey, well-being, and academic success. You can ask me about study habits, clearing backlogs, managing exam anxiety, or improving your attendance!"
        
    return {'reply': reply}

