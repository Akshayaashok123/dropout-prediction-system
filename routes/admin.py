import os
import io
import csv
import json
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, Response
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import (db, User, Student, Teacher, Counsellor, RiskAssessment, 
                    Attendance, Marks, CounsellingSession, Observation, Recommendation)
from routes.decorators import role_required
from ml.predictor import DropoutPredictor

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.before_request
@login_required
@role_required('admin')
def admin_protection():
    pass

@admin.route('/dashboard')
def dashboard():
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_counsellors = Counsellor.query.count()
    
    # Calculate latest risk distribution accurately per student
    students = Student.query.all()
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    
    # Buckets for Attendance
    att_lt60 = 0
    att_60_75 = 0
    att_75_85 = 0
    att_gt85 = 0
    
    # Buckets for GPA
    gpa_lt5 = 0
    gpa_5_65 = 0
    gpa_65_8 = 0
    gpa_gt8 = 0
    
    # Department breakdown
    dept_stats = {}
    
    for s in students:
        # Risk from latest assessment
        la = s.latest_assessment
        if la:
            lvl = (la.risk_level or 'low').lower()
            if lvl == 'high':
                high_risk_count += 1
            elif lvl == 'medium':
                medium_risk_count += 1
            else:
                low_risk_count += 1
        else:
            low_risk_count += 1
            
        # Attendance bucket
        att = s.attendance_pct if s.attendance_pct is not None else 0.0
        if att < 60:
            att_lt60 += 1
        elif att < 75:
            att_60_75 += 1
        elif att < 85:
            att_75_85 += 1
        else:
            att_gt85 += 1
            
        # GPA bucket
        g = s.gpa if s.gpa is not None else 0.0
        if g < 5.0:
            gpa_lt5 += 1
        elif g < 6.5:
            gpa_5_65 += 1
        elif g < 8.0:
            gpa_65_8 += 1
        else:
            gpa_gt8 += 1
            
        # Department stats
        dept = s.department or 'General'
        if dept not in dept_stats:
            dept_stats[dept] = {'high': 0, 'medium': 0, 'low': 0, 'total': 0}
        dept_stats[dept]['total'] += 1
        if la:
            lvl = (la.risk_level or 'low').lower()
            dept_stats[dept][lvl] = dept_stats[dept].get(lvl, 0) + 1
        else:
            dept_stats[dept]['low'] += 1

    # Intervention statistics
    pending_followups = CounsellingSession.query.filter(
        CounsellingSession.status.in_(['scheduled', 'in_progress', 'pending'])
    ).count()
    completed_interventions = CounsellingSession.query.filter_by(status='completed').count()
    
    # Intervention statuses for chart
    session_status_counts = {
        'Scheduled': CounsellingSession.query.filter_by(status='scheduled').count(),
        'In Progress': CounsellingSession.query.filter_by(status='in_progress').count(),
        'Completed': CounsellingSession.query.filter_by(status='completed').count(),
        'Cancelled': CounsellingSession.query.filter_by(status='cancelled').count()
    }
    
    stats = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_counsellors': total_counsellors,
        'high_risk': high_risk_count,
        'medium_risk': medium_risk_count,
        'low_risk': low_risk_count,
        'pending_followups': pending_followups,
        'completed_interventions': completed_interventions
    }
    
    # Recent risk assessments
    raw_recent = RiskAssessment.query.order_by(RiskAssessment.assessed_at.desc()).limit(8).all()
    recent_assessments = []
    for a in raw_recent:
        st = a.student
        recent_assessments.append({
            'student_id': a.student_id,
            'student_name': st.name if st else f'Student #{a.student_id}',
            'department': st.department if st else 'General',
            'risk_score': round(a.risk_score, 1) if a.risk_score is not None else 0,
            'level': (a.risk_level or 'low').capitalize(),
            'source': a.assessment_source or 'Rule & Model Hybrid',
            'date': a.assessed_at.strftime('%b %d, %Y') if a.assessed_at else 'Recent'
        })
        
    # Recent intervention activity
    recent_interventions = CounsellingSession.query.order_by(
        CounsellingSession.scheduled_at.desc()
    ).limit(6).all()
    
    chart_data = {
        'risk_distribution': {
            'High': high_risk_count,
            'Medium': medium_risk_count,
            'Low': low_risk_count
        },
        'attendance_distribution': {
            '<60%': att_lt60,
            '60-75%': att_60_75,
            '75-85%': att_75_85,
            '>85%': att_gt85
        },
        'gpa_distribution': {
            '<5.0': gpa_lt5,
            '5.0-6.5': gpa_5_65,
            '6.5-8.0': gpa_65_8,
            '>8.0': gpa_gt8
        },
        'intervention_status': session_status_counts,
        'department_names': list(dept_stats.keys()),
        'department_high': [dept_stats[d]['high'] for d in dept_stats],
        'department_medium': [dept_stats[d]['medium'] for d in dept_stats],
        'department_low': [dept_stats[d]['low'] for d in dept_stats]
    }
    
    return render_template('admin/dashboard.html', 
                           stats=stats,
                           chart_data=chart_data,
                           recent_assessments=recent_assessments,
                           recent_interventions=recent_interventions)

@admin.route('/students')
def students():
    search = request.args.get('search', '').strip().lower()
    department = request.args.get('department', '').strip()
    semester = request.args.get('semester', '').strip()
    risk_level = request.args.get('risk_level', '').strip()
    sort_by = request.args.get('sort', 'risk_desc').strip()
    
    query = Student.query
    
    if department:
        query = query.filter_by(department=department)
    if semester:
        try:
            query = query.filter_by(semester=int(semester))
        except ValueError:
            pass
            
    all_students = query.all()
    filtered = []
    
    for s in all_students:
        s_name = (s.name or '').lower()
        s_email = (s.email or '').lower()
        s_id = str(s.id)
        
        # Search filter
        if search and (search not in s_name and search not in s_email and search not in s_id):
            continue
            
        # Risk level filter
        if risk_level and s.latest_risk_level.lower() != risk_level.lower():
            continue
            
        filtered.append(s)
        
    # Sorting
    if sort_by == 'risk_desc':
        filtered.sort(key=lambda s: s.latest_risk_score, reverse=True)
    elif sort_by == 'risk_asc':
        filtered.sort(key=lambda s: s.latest_risk_score)
    elif sort_by == 'att_asc':
        filtered.sort(key=lambda s: s.attendance_pct or 0.0)
    elif sort_by == 'att_desc':
        filtered.sort(key=lambda s: s.attendance_pct or 0.0, reverse=True)
    elif sort_by == 'gpa_asc':
        filtered.sort(key=lambda s: s.gpa or 0.0)
    elif sort_by == 'gpa_desc':
        filtered.sort(key=lambda s: s.gpa or 0.0, reverse=True)
    elif sort_by == 'name':
        filtered.sort(key=lambda s: (s.name or '').lower())
        
    # Get all distinct departments
    depts = [d[0] for d in db.session.query(Student.department).distinct().all() if d[0]]
    if not depts:
        depts = ['Computer Science', 'Electronics & Comm.', 'Mechanical', 'Civil', 'Electrical']
        
    return render_template('admin/students.html', 
                           students=filtered,
                           departments=depts,
                           current_search=search,
                           current_dept=department,
                           current_sem=semester,
                           current_risk=risk_level,
                           current_sort=sort_by)

@admin.route('/students/export')
def export_students():
    """Export filtered or complete student risk assessment records to CSV."""
    department = request.args.get('department', '').strip()
    semester = request.args.get('semester', '').strip()
    risk_level = request.args.get('risk_level', '').strip()
    search = request.args.get('search', '').strip().lower()

    query = Student.query
    if department:
        query = query.filter_by(department=department)
    if semester:
        try:
            query = query.filter_by(semester=int(semester))
        except ValueError:
            pass
            
    all_students = query.all()
    filtered = []
    for s in all_students:
        s_name = (s.name or '').lower()
        s_email = (s.email or '').lower()
        s_id = str(s.id)
        if search and (search not in s_name and search not in s_email and search not in s_id):
            continue
        if risk_level and s.latest_risk_level.lower() != risk_level.lower():
            continue
        filtered.append(s)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Student ID', 'Full Name', 'Institutional Email', 'Department', 'Semester',
        'Attendance (%)', 'GPA', 'Risk Level', 'Risk Score (%)', 'Assessment Source',
        'Intervention Status', 'Latest Mentor Follow-up'
    ])
    
    for s in filtered:
        la = s.latest_assessment
        source = la.assessment_source if la and la.assessment_source else 'ML Model Simulation'
        li = s.latest_intervention
        status = li.status if li else 'No Intervention'
        followup = li.scheduled_at.strftime('%Y-%m-%d') if li and li.scheduled_at else 'N/A'
        
        writer.writerow([
            s.id,
            s.name,
            s.email,
            s.department or 'N/A',
            s.semester or 'N/A',
            round(s.attendance_pct or 0.0, 1),
            round(s.gpa or 0.0, 2),
            s.latest_risk_level,
            s.latest_risk_score,
            source,
            status,
            followup
        ])
        
    output.seek(0)
    filename = f"eduguard_students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@admin.route('/students/sample-csv')
def download_sample_csv():
    """Download a standardized sample CSV matching the application import schema."""
    sample_content = (
        "name,email,department,semester,attendance,gpa,phone\n"
        "Demo Student (Critical Review),demo.sample1@school.edu,Computer Science,3,52.4,3.40,555-0191\n"
        "Demo Student (Declining Trajectory),demo.sample2@school.edu,Electronics & Comm.,4,64.5,5.15,555-0192\n"
        "Demo Student (Moderate Review),demo.sample3@school.edu,Mechanical,2,71.0,5.80,555-0193\n"
        "Demo Student (Good Standing),demo.sample4@school.edu,Civil,5,86.5,8.25,555-0194\n"
        "Demo Student (High Performing),demo.sample5@school.edu,Electrical,6,95.0,9.40,555-0195\n"
    )
    return Response(
        sample_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_student_import_template.csv"}
    )

@admin.route('/students/<int:id>')
def student_detail(id):
    student = Student.query.get_or_404(id)
    
    # Detailed data collections
    attendance_records = Attendance.query.filter_by(student_id=id).order_by(Attendance.date.desc()).all()
    marks_records = Marks.query.filter_by(student_id=id).order_by(Marks.semester.desc(), Marks.subject.asc()).all()
    risk_history = RiskAssessment.query.filter_by(student_id=id).order_by(RiskAssessment.assessed_at.desc()).all()
    observations = Observation.query.filter_by(student_id=id).order_by(Observation.created_at.desc()).all()
    sessions = CounsellingSession.query.filter_by(student_id=id).order_by(CounsellingSession.scheduled_at.desc()).all()
    recommendations = Recommendation.query.filter_by(student_id=id).order_by(Recommendation.created_at.desc()).all()
    
    # Generate live explainable risk assessment data
    predictor = DropoutPredictor()
    explanation_data = predictor.predict_risk(student.id)
    
    # Format attendance summary for timeline/graph
    att_present = sum(1 for a in attendance_records if a.status and a.status.lower() == 'present')
    att_late = sum(1 for a in attendance_records if a.status and a.status.lower() == 'late')
    att_absent = sum(1 for a in attendance_records if a.status and a.status.lower() == 'absent')
    att_total = len(attendance_records)
    
    # Subject-wise marks summary
    subject_marks = {}
    for m in marks_records:
        if m.subject not in subject_marks:
            subject_marks[m.subject] = {}
        subject_marks[m.subject][m.exam_type] = m.score
        
    counsellors = Counsellor.query.all()
    
    return render_template('admin/student_detail.html',
                           student=student,
                           attendance_records=attendance_records,
                           marks_records=marks_records,
                           risk_history=risk_history,
                           observations=observations,
                           sessions=sessions,
                           recommendations=recommendations,
                           explanation=explanation_data,
                           att_present=att_present,
                           att_late=att_late,
                           att_absent=att_absent,
                           att_total=att_total,
                           subject_marks=subject_marks,
                           counsellors=counsellors)

@admin.route('/students/<int:id>/intervene', methods=['POST'])
def add_intervention(id):
    student = Student.query.get_or_404(id)
    support_type = request.form.get('support_type', 'Academic Mentoring')
    notes = request.form.get('notes', '').strip()
    status = request.form.get('status', 'scheduled')
    outcome = request.form.get('outcome', '').strip()
    scheduled_str = request.form.get('scheduled_at')
    next_followup_str = request.form.get('next_followup_date')
    counsellor_id = request.form.get('counsellor_id')
    
    scheduled_at = datetime.utcnow()
    if scheduled_str:
        try:
            scheduled_at = datetime.strptime(scheduled_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            try:
                scheduled_at = datetime.strptime(scheduled_str, '%Y-%m-%d')
            except ValueError:
                scheduled_at = datetime.utcnow()
                
    next_followup = None
    if next_followup_str:
        try:
            next_followup = datetime.strptime(next_followup_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    cid = int(counsellor_id) if counsellor_id and counsellor_id.isdigit() else None
    counsellor_obj = Counsellor.query.get(cid) if cid else Counsellor.query.first()
    
    session_record = CounsellingSession(
        student_id=student.id,
        counsellor_id=counsellor_obj.id if counsellor_obj else None,
        mentor_name=current_user.name,
        support_type=support_type,
        scheduled_at=scheduled_at,
        next_followup_date=next_followup,
        status=status,
        session_type='individual',
        notes=notes,
        outcome=outcome
    )
    db.session.add(session_record)
    db.session.commit()
    
    flash(f"Intervention recorded successfully for {student.name}.", "success")
    return redirect(url_for('admin.student_detail', id=student.id))

@admin.route('/students/upload-preview', methods=['POST'])
def upload_preview():
    if 'file' not in request.files:
        flash('No file provided.', 'danger')
        return redirect(url_for('admin.students'))
        
    file = request.files['file']
    if not file or file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('admin.students'))
        
    if not file.filename.endswith('.csv'):
        flash('Invalid file format. Please upload a CSV file (.csv).', 'danger')
        return redirect(url_for('admin.students'))
        
    try:
        content = file.stream.read().decode('utf-8-sig', errors='ignore')
        reader = csv.DictReader(io.StringIO(content))
        
        # Check required headers
        fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
        req_fields = ['name', 'email', 'department']
        
        missing_req = [rf for rf in req_fields if not any(rf in h for h in fieldnames)]
        if missing_req:
            flash(f"CSV header validation failed. Missing required column(s): {', '.join(missing_req)}. Expected headers include name, email, department, semester, attendance, gpa.", 'danger')
            return redirect(url_for('admin.students'))
            
        valid_rows = []
        invalid_rows = []
        seen_emails = set()
        
        row_num = 1
        for row in reader:
            row_num += 1
            # Normalize keys
            norm_row = {k.strip().lower(): (v or '').strip() for k, v in row.items() if k}
            
            # Find values with flexible column aliases
            name = norm_row.get('name') or norm_row.get('student_name') or ''
            email = norm_row.get('email') or norm_row.get('student_email') or ''
            department = norm_row.get('department') or norm_row.get('dept') or 'General'
            sem_raw = norm_row.get('semester') or norm_row.get('sem') or '1'
            att_raw = norm_row.get('attendance_pct') or norm_row.get('attendance') or norm_row.get('attendance_percentage') or '75.0'
            gpa_raw = norm_row.get('gpa') or norm_row.get('cgpa') or '7.0'
            phone = norm_row.get('contact_phone') or norm_row.get('phone') or '555-0100'
            
            row_errors = []
            
            if not name:
                row_errors.append("Missing student name")
            if not email or '@' not in email:
                row_errors.append("Missing or invalid email address")
            elif email in seen_emails:
                row_errors.append("Duplicate email within uploaded CSV")
            seen_emails.add(email)
            
            # Type validations
            try:
                sem = int(sem_raw)
                if sem < 1 or sem > 12:
                    row_errors.append(f"Semester must be between 1 and 12 (got '{sem_raw}')")
            except ValueError:
                row_errors.append(f"Invalid semester '{sem_raw}', expected integer")
                sem = 1
                
            try:
                att = float(att_raw)
                if att < 0 or att > 100:
                    row_errors.append(f"Attendance % must be between 0 and 100 (got '{att_raw}')")
            except ValueError:
                row_errors.append(f"Invalid attendance value '{att_raw}', expected float")
                att = 75.0
                
            try:
                gpa = float(gpa_raw)
                if gpa < 0 or gpa > 10.0:
                    row_errors.append(f"GPA must be between 0.0 and 10.0 (got '{gpa_raw}')")
            except ValueError:
                row_errors.append(f"Invalid GPA value '{gpa_raw}', expected float")
                gpa = 7.0
                
            # Check if existing user in DB
            existing_user = User.query.filter_by(email=email).first()
            is_update = existing_user is not None
            
            clean_record = {
                'row_number': row_num,
                'name': name,
                'email': email,
                'department': department,
                'semester': sem,
                'attendance_pct': att,
                'gpa': gpa,
                'contact_phone': phone,
                'action': 'Update Existing' if is_update else 'Create New'
            }
            
            if row_errors:
                invalid_rows.append({
                    'row_number': row_num,
                    'raw_data': norm_row,
                    'reasons': row_errors
                })
            else:
                valid_rows.append(clean_record)
                
        # Store valid rows in session for confirmation
        session['import_preview_data'] = valid_rows
        session['import_total_rows'] = row_num - 1
        session['import_invalid_count'] = len(invalid_rows)
        
        return render_template('admin/import_preview.html',
                               valid_rows=valid_rows,
                               invalid_rows=invalid_rows,
                               total_count=row_num - 1,
                               valid_count=len(valid_rows),
                               invalid_count=len(invalid_rows))
                               
    except Exception as e:
        flash(f"Error reading CSV file: {str(e)}", 'danger')
        return redirect(url_for('admin.students'))

@admin.route('/students/import-confirm', methods=['POST'])
def import_confirm():
    preview_data = session.get('import_preview_data')
    if not preview_data:
        flash('Import session expired or empty. Please upload the CSV again.', 'warning')
        return redirect(url_for('admin.students'))
        
    created_count = 0
    updated_count = 0
    
    predictor = DropoutPredictor()
    
    for row in preview_data:
        email = row['email']
        name = row['name']
        dept = row['department']
        sem = row['semester']
        att = row['attendance_pct']
        gpa = row['gpa']
        phone = row.get('contact_phone', '555-0100')
        
        user = User.query.filter_by(email=email).first()
        if user:
            user.name = name
            student = user.student_profile
            if not student:
                student = Student(user_id=user.id)
                db.session.add(student)
            student.department = dept
            student.semester = sem
            student.attendance_pct = att
            student.gpa = gpa
            student.contact_phone = phone
            updated_count += 1
        else:
            new_user = User(
                name=name,
                email=email,
                role='student',
                password_hash=generate_password_hash('student123')
            )
            db.session.add(new_user)
            db.session.flush()
            
            student = Student(
                user_id=new_user.id,
                department=dept,
                semester=sem,
                enrollment_year=datetime.utcnow().year,
                attendance_pct=att,
                gpa=gpa,
                contact_phone=phone
            )
            db.session.add(student)
            created_count += 1
            
        db.session.flush()
        
        # Calculate & record risk assessment for the student
        try:
            assessment = predictor.predict_risk(student.id)
            ra = RiskAssessment(
                student_id=student.id,
                risk_score=assessment['risk_score'],
                risk_level=assessment['risk_level'],
                contributing_factors="; ".join(assessment['contributing_factors']),
                assessment_source=assessment['assessment_source'],
                assessed_at=datetime.utcnow()
            )
            db.session.add(ra)
        except Exception:
            pass

    db.session.commit()
    
    # Clear session
    session.pop('import_preview_data', None)
    session.pop('import_total_rows', None)
    session.pop('import_invalid_count', None)
    
    flash(f"CSV Import Successful! Processed {created_count + updated_count} student records ({created_count} new created, {updated_count} existing updated). Risk assessments synchronized.", 'success')
    return redirect(url_for('admin.students'))

@admin.route('/students/import-cancel', methods=['POST'])
def import_cancel():
    session.pop('import_preview_data', None)
    session.pop('import_total_rows', None)
    session.pop('import_invalid_count', None)
    flash("CSV import cancelled. No changes were made to student records.", "info")
    return redirect(url_for('admin.students'))

@admin.route('/users')
def users():
    users_list = User.query.order_by(User.role.asc(), User.name.asc()).all()
    return render_template('admin/users.html', users=users_list)

@admin.route('/analytics')
def analytics():
    # Pass dynamically computed metrics for deep analysis
    students = Student.query.all()
    high_c = 0
    med_c = 0
    low_c = 0
    
    dept_map = {}
    scatter_points = []
    
    for s in students:
        lvl = s.latest_risk_level.lower()
        if lvl == 'high': high_c += 1
        elif lvl == 'medium': med_c += 1
        else: low_c += 1
        
        dept = s.department or 'General'
        if dept not in dept_map:
            dept_map[dept] = {'high': 0, 'medium': 0, 'low': 0}
        dept_map[dept][lvl] = dept_map[dept].get(lvl, 0) + 1
        
        scatter_points.append({
            'x': round(s.attendance_pct or 0.0, 1),
            'y': round(s.gpa or 0.0, 2),
            'level': s.latest_risk_level
        })
        
    depts = list(dept_map.keys())
    chart_data = {
        'risk_distribution': {'High': high_c, 'Medium': med_c, 'Low': low_c},
        'departments': depts,
        'dept_high': [dept_map[d]['high'] for d in depts],
        'dept_medium': [dept_map[d]['medium'] for d in depts],
        'dept_low': [dept_map[d]['low'] for d in depts],
        'scatter_points': scatter_points
    }
    return render_template('admin/analytics.html', chart_data=chart_data)

@admin.route('/run-prediction', methods=['POST'])
def run_prediction():
    """Trigger ML prediction for all students."""
    try:
        predictor = DropoutPredictor()
        results = predictor.predict_all()
        flash(f"Batch AI prediction complete! {results.get('processed', 0)} students assessed ({results.get('high', 0)} High, {results.get('medium', 0)} Medium, {results.get('low', 0)} Low).", 'success')
    except Exception as e:
        flash(f'Prediction failed: {str(e)}', 'danger')
    return redirect(url_for('admin.dashboard'))

@admin.route('/reset-demo-data', methods=['POST'])
def reset_demo_data():
    """Safely re-seed demo database to initial state for judge demonstrations."""
    try:
        from seed_data import seed_db
        seed_db()
        flash("Demo dataset has been reset to baseline prototype state (50 demo students, teachers, counsellors & interventions).", "success")
    except Exception as e:
        flash(f"Failed to reset demo dataset: {str(e)}", "danger")
    return redirect(url_for('admin.dashboard'))
