import os
import io
import pytest
from datetime import datetime, date
from app import create_app
from models import db, User, Student, Teacher, Counsellor, RiskAssessment, Attendance, Marks, CounsellingSession, Recommendation
from ml.predictor import DropoutPredictor

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def login_as(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

# 1. Prediction Flow Tests
def test_predictor_model_or_rules(app):
    with app.app_context():
        predictor = DropoutPredictor()
        test_student = Student.query.first()
        assert test_student is not None, "At least one student should exist from seed data"
        
        assessment = predictor.predict_risk(test_student.id)
        assert 'risk_score' in assessment
        assert 'risk_level' in assessment
        assert assessment['risk_level'] in ['low', 'medium', 'high']
        assert 'contributing_factors' in assessment
        assert 'mentor_review_reason' in assessment
        assert 'suggested_next_steps' in assessment
        assert 'assessment_source' in assessment
        assert isinstance(assessment['risk_score'], (int, float))
        assert 0 <= assessment['risk_score'] <= 100

def test_rule_based_fallback(app):
    with app.app_context():
        predictor = DropoutPredictor()
        # High risk dummy profile
        high_risk_feats = {
            'attendance_pct': 45.0,
            'gpa': 3.2,
            'internal_marks_avg': 40.0,
            'semester_marks_avg': 35.0,
            'assignment_score_avg': 40.0,
            'backlogs_count': 3,
            'attendance_trend': -0.25,
            'marks_trend': -0.1,
            'engagement_score': 42.5
        }
        score, factors = predictor._rule_based_predict(high_risk_feats)
        assert score > 65
        assert len(factors) > 0
        factor_names = [f['factor'] for f in factors]
        assert 'Critical Attendance Deficit' in factor_names
        assert 'Academic Performance Concern' in factor_names

# 2. Authentication & Protected Routes
def test_admin_dashboard_access(client):
    # Unauthenticated should redirect to login
    res = client.get('/admin/dashboard')
    assert res.status_code == 302
    assert '/login' in res.location

    # Login as admin
    login_res = login_as(client, 'admin@school.edu', 'admin123')
    assert login_res.status_code == 200
    
    # Access dashboard
    dash_res = client.get('/admin/dashboard')
    assert dash_res.status_code == 200
    assert b'Institutional Overview' in dash_res.data or b'Surveillance' in dash_res.data
    assert b'Total Enrolled' in dash_res.data

def test_admin_student_directory_filters(client):
    login_as(client, 'admin@school.edu', 'admin123')
    
    # Base directory
    res = client.get('/admin/students')
    assert res.status_code == 200
    assert b'Student Cohort Directory' in res.data
    
    # Filter by risk level
    res_high = client.get('/admin/students?risk_level=High')
    assert res_high.status_code == 200
    
    # Sort by attendance
    res_sort = client.get('/admin/students?sort=att_asc')
    assert res_sort.status_code == 200

def test_admin_student_detail(client, app):
    login_as(client, 'admin@school.edu', 'admin123')
    with app.app_context():
        student = Student.query.first()
        student_id = student.id
        
    res = client.get(f'/admin/students/{student_id}')
    assert res.status_code == 200
    assert b'Early-Warning Assessment' in res.data
    assert b'Intervention Tracking' in res.data

# 3. CSV Import Preview & Validation
def test_csv_import_workflow(client, app):
    login_as(client, 'admin@school.edu', 'admin123')
    
    # Construct a valid and invalid CSV
    csv_content = (
        "name,email,department,semester,attendance,gpa,phone\n"
        "Valid Test Student,validtest@school.edu,Computer Science,3,82.5,7.8,555-1234\n"
        "Bad GPA Student,badgpa@school.edu,Mechanical,2,70.0,14.5,555-5678\n"
    )
    
    data = {
        'file': (io.BytesIO(csv_content.encode('utf-8')), 'test_students.csv')
    }
    
    res = client.post('/admin/students/upload-preview', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert res.status_code == 200
    assert b'Staged CSV Import Preview' in res.data
    assert b'Valid Rows (Ready)' in res.data
    assert b'Rejected Rows' in res.data
    assert b'Validation Failures' in res.data
    assert b'GPA must be between 0.0 and 10.0' in res.data

    # Confirm import
    confirm_res = client.post('/admin/students/import-confirm', follow_redirects=True)
    assert confirm_res.status_code == 200
    assert b'CSV Import Successful' in confirm_res.data
    
    # Verify student now exists in DB
    with app.app_context():
        imported = User.query.filter_by(email='validtest@school.edu').first()
        assert imported is not None
        assert imported.name == 'Valid Test Student'
        assert imported.student_profile.attendance_pct == 82.5

# 4. Counsellor Mentor Action Queue & Interventions
def test_counsellor_action_queue(client):
    login_as(client, 'counsellor1@school.edu', 'counsellor123')
    
    # Dashboard
    res = client.get('/counsellor/dashboard')
    assert res.status_code == 200
    assert b'Counsellor Desk' in res.data
    
    # Action Queue
    queue_res = client.get('/counsellor/referrals')
    assert queue_res.status_code == 200
    assert b'Mentor Action Queue' in queue_res.data
    assert b'Alert Reason' in queue_res.data

def test_intervention_crud_lifecycle(client, app):
    login_as(client, 'counsellor1@school.edu', 'counsellor123')
    with app.app_context():
        student = Student.query.first()
        student_id = student.id
        initial_count = CounsellingSession.query.filter_by(student_id=student_id).count()
        
    # Create intervention
    create_data = {
        'support_type': 'Attendance Barrier Review',
        'scheduled_at': '2026-11-05T14:30',
        'next_followup_date': '2026-11-19',
        'status': 'scheduled',
        'notes': 'Discussion on transit hurdles from northern suburb.',
        'outcome': 'Agreed to explore morning bus pass.'
    }
    create_res = client.post(f'/counsellor/students/{student_id}/session', data=create_data, follow_redirects=True)
    assert create_res.status_code == 200
    
    with app.app_context():
        new_count = CounsellingSession.query.filter_by(student_id=student_id).count()
        assert new_count == initial_count + 1
        created_session = CounsellingSession.query.filter_by(student_id=student_id).order_by(CounsellingSession.id.desc()).first()
        assert created_session.support_type == 'Attendance Barrier Review'
        assert created_session.status == 'scheduled'
        session_id = created_session.id

    # Update intervention
    update_data = {
        'support_type': 'Attendance Barrier Review',
        'status': 'completed',
        'notes': 'Followed up with student. Bus pass acquired, attendance improved.',
        'outcome': 'Resolved barrier successfully.',
        'next_followup_date': ''
    }
    update_res = client.post(f'/counsellor/sessions/{session_id}/update', data=update_data, follow_redirects=True)
    assert update_res.status_code == 200
    
    with app.app_context():
        updated_session = CounsellingSession.query.get(session_id)
        assert updated_session.status == 'completed'
        assert 'Resolved barrier' in updated_session.outcome

# 5. Teacher Role & Alerts
def test_teacher_dashboard_and_alerts(client):
    login_as(client, 'teacher1@school.edu', 'teacher123')
    
    dash_res = client.get('/teacher/dashboard')
    assert dash_res.status_code == 200
    
    alerts_res = client.get('/teacher/alerts')
    assert alerts_res.status_code == 200
    assert b'Department Action Alerts' in alerts_res.data
    assert b'Students Requiring Classroom Attention' in alerts_res.data

# 6. Student Wellness Portal
def test_student_dashboard(client):
    login_as(client, 'student1@school.edu', 'student123')
    
    dash_res = client.get('/student/dashboard')
    assert dash_res.status_code == 200
    assert b'Academic Wellness Index' in dash_res.data
    assert b'out of 100' in dash_res.data
    
    recs_res = client.get('/student/recommendations')
    assert recs_res.status_code == 200

def test_admin_export_csv(client):
    login_as(client, 'admin@school.edu', 'admin123')
    res = client.get('/admin/students/export?risk_level=High')
    assert res.status_code == 200
    assert res.headers['Content-Type'].startswith('text/csv')
    csv_text = res.data.decode('utf-8')
    assert 'Student ID,Full Name,Institutional Email' in csv_text
    assert 'Attendance (%)' in csv_text

def test_teacher_student_detail_charts(client, app):
    login_as(client, 'teacher1@school.edu', 'teacher123')
    with app.app_context():
        student = Student.query.first()
        student_id = student.id
    res = client.get(f'/teacher/students/{student_id}')
    assert res.status_code == 200
    assert b'Attendance (30 Days)' in res.data
    assert b'Subject Marks' in res.data
    assert b'attChart' in res.data
    assert b'marksChart' in res.data

def test_student_sessions_and_resources(client, app):
    login_as(client, 'student1@school.edu', 'student123')
    
    # Resources page
    res_page = client.get('/student/resources')
    assert res_page.status_code == 200
    assert b'Academic &amp; Wellness Resources' in res_page.data or b'Academic & Wellness Resources' in res_page.data
    assert b'Time Management' in res_page.data
    
    # Sessions page
    sess_page = client.get('/student/sessions')
    assert sess_page.status_code == 200
    assert b'My Counselling &amp; Mentoring Sessions' in sess_page.data or b'My Counselling & Mentoring Sessions' in sess_page.data
    
    # Request help POST
    help_post = client.post('/student/request-help', data={
        'category': 'Academic Tutoring',
        'message': 'Need assistance with advanced algorithms before midterms.'
    }, follow_redirects=True)
    assert help_post.status_code == 200
    assert b'Your request for help has been submitted' in help_post.data

def test_complete_demo_scenario(client, app):
    """Full judge walkthrough simulating end-to-end evaluation flow."""
    # Step 1: Admin login & KPIs
    login_as(client, 'admin@school.edu', 'admin123')
    dash = client.get('/admin/dashboard')
    assert dash.status_code == 200
    assert b'Total Enrolled' in dash.data
    
    # Step 2: Student directory filter
    filtered = client.get('/admin/students?risk_level=High&sort=att_asc')
    assert filtered.status_code == 200
    
    # Step 3: Counsellor logs in, picks student from action queue, logs session
    login_as(client, 'counsellor1@school.edu', 'counsellor123')
    queue = client.get('/counsellor/referrals')
    assert queue.status_code == 200
    
    with app.app_context():
        target_student = Student.query.first()
        t_id = target_student.id
        
    sess_create = client.post(f'/counsellor/students/{t_id}/session', data={
        'support_type': 'Remedial Tutoring Referral',
        'scheduled_at': '2026-11-10T10:00',
        'next_followup_date': '2026-11-24',
        'status': 'scheduled',
        'notes': 'Referred to department peer tutor for Mathematics.',
        'outcome': ''
    }, follow_redirects=True)
    assert sess_create.status_code == 200
    
    # Step 4: Verify session shows in Counsellor Sessions hub
    sessions_hub = client.get('/counsellor/sessions')
    assert sessions_hub.status_code == 200
    assert b'Remedial Tutoring Referral' in sessions_hub.data
    
    # Step 5: Teacher logs in, observes student, files referral
    login_as(client, 'teacher1@school.edu', 'teacher123')
    obs_post = client.post(f'/teacher/students/{t_id}/observe', data={
        'category': 'academic',
        'content': 'Student showed active participation in today laboratory session.'
    }, follow_redirects=True)
    assert obs_post.status_code == 200
    
    # Step 6: Student logs in, interacts with chatbot & views session
    login_as(client, 'student1@school.edu', 'student123')
    chat_post = client.post('/student/chatbot-api', json={'message': 'how can I improve attendance?'})
    assert chat_post.status_code == 200
    assert 'attendance' in chat_post.get_json()['reply'].lower()


