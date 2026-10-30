import os
import random
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash
from models import (db, User, Student, Teacher, Counsellor, Attendance, 
                    Marks, RiskAssessment, CounsellingSession, Observation,
                    Recommendation, Notification)
from ml.predictor import DropoutPredictor

DEPARTMENTS = ['Computer Science', 'Electronics & Comm.', 'Mechanical', 'Civil', 'Electrical']

DEPARTMENT_SUBJECTS = {
    'Computer Science': [
        'Programming in Python', 'Data Structures & Algorithms', 
        'Database Management Systems', 'Operating Systems', 'Computer Networks'
    ],
    'Electronics & Comm.': [
        'Signals & Systems', 'Digital Electronics', 
        'Microprocessors & Microcontrollers', 'Analog Communication', 'VLSI Design'
    ],
    'Mechanical': [
        'Engineering Thermodynamics', 'Fluid Mechanics', 
        'Strength of Materials', 'Manufacturing Processes', 'Kinematics of Machinery'
    ],
    'Civil': [
        'Structural Analysis', 'Geotechnical Engineering', 
        'Surveying & Geomatics', 'Concrete Technology', 'Hydraulics & Water Resources'
    ],
    'Electrical': [
        'Circuit Theory & Networks', 'Electrical Machines', 
        'Power Systems Analysis', 'Control Systems Engineering', 'Power Electronics'
    ]
}

# 100 realistic, diverse fictional student names for demonstration
STUDENT_NAMES = [
    "Aarav Sharma", "Diya Patel", "Rohan Verma", "Ananya Iyer", "Vikram Singh",
    "Priya Nair", "Sneha Kulkarni", "Rahul Gupta", "Fatima Khan", "Arjun Das",
    "Neha Sharma", "Siddharth Roy", "Kavya Menon", "Aditya Joshi", "Pooja Reddy",
    "Tarun Mehta", "Meera Nair", "Karan Kapoor", "Ishita Sen", "Devendra Chauhan",
    "Tanvi Deshmukh", "Nikhil Bhat", "Shreya Pillai", "Harsh Vardhan", "Riya Mukherjee",
    "Manish Tiwari", "Ankita Rao", "Deepak Kumar", "Swati Hegde", "Gaurav Malhotra",
    "Simran Kaur", "Abhinav Mishra", "Divya Nambiar", "Yashwant Rao", "Alia Siddiqui",
    "Pranav Saxena", "Nandini Ghosh", "Varun Shenoy", "Bhavna Jain", "Kartik Chandra",
    "Pallavi Patil", "Mohit Bansal", "Zoya Farooqui", "Rakesh Yadav", "Sunita Biswas",
    "Akash Agarwal", "Kritika Soni", "Sumit Chawla", "Ritu Rawat", "Hemant Pandey",
    "Pooja Verma", "Karthik Iyer", "Sneha Patel", "Ananya Das", "Rohit Nair",
    "Aishwarya Rao", "Vivek Menon", "Madhuri Sen", "Mayank Trivedi", "Lavanya Krishnan",
    "Tushar Shinde", "Preeti Dubey", "Girish Pai", "Shilpa Shetty", "Ravi Shankar",
    "Geeta Sundaram", "Umesh Chandra", "Komal Arora", "Saurabh Negi", "Juhi Parmar",
    "Bhavesh Pandya", "Monika Solanki", "Dinesh Rathore", "Kiran Mazumdar", "Sachin Kale",
    "Sapna Rathi", "Vikas Bhasin", "Rashmi Sethi", "Gautam Bose", "Namrata Gokhale",
    "Chirag Dave", "Vidya Balan", "Sanjay Mahajan", "Poonam Jha", "Anil Kumar",
    "Archana Puran", "Rajesh Khanna", "Suman Lata", "Mukesh Verma", "Rekha Ganesan",
    "Pradeep Nayak", "Latika Soni", "Kishore Bhende", "Asha Parekh", "Sunil Grover",
    "Kapil Chhabra", "Sania Hashmi", "Abhinav Kashyap", "Mary DSouza", "Rajeshwari Iyer"
]

def seed_db(force_recreate=True):
    """
    Populate database with approximately 100 fictional student records,
    historical attendance, academic marks, explainable assessments, and counselling interventions.
    """
    if force_recreate:
        print("Dropping and recreating database tables...")
        db.drop_all()
        db.create_all()

    # 1. System Administrator
    admin = User.query.filter_by(email='admin@school.edu').first()
    if not admin:
        print("Seeding System Administrator...")
        admin = User(name='System Admin', email='admin@school.edu', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

    # 2. Faculty / Teachers (one for each key department)
    teachers = []
    teacher_configs = [
        ('Dr. Ramesh Rao (Faculty Advisor)', 'teacher1@school.edu', 'Computer Science'),
        ('Prof. Sunita Deshmukh', 'teacher2@school.edu', 'Electronics & Comm.'),
        ('Dr. Arvind Menon', 'teacher3@school.edu', 'Mechanical')
    ]
    for name, email, dept in teacher_configs:
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(name=name, email=email, role='teacher')
            u.set_password('teacher123')
            db.session.add(u)
            db.session.flush()
            t = Teacher(user_id=u.id, department=dept)
            db.session.add(t)
            teachers.append(t)
        else:
            teachers.append(u.teacher_profile)

    # 3. Student Counsellors / Mentors
    counsellors = []
    counsellor_configs = [
        ('Dr. Anita Sharma', 'counsellor1@school.edu', 'Academic Distress & Attendance Remediation'),
        ('Mr. David DSilva', 'counsellor2@school.edu', 'Financial Aid & Student Wellness')
    ]
    for name, email, spec in counsellor_configs:
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(name=name, email=email, role='counsellor')
            u.set_password('counsellor123')
            db.session.add(u)
            db.session.flush()
            c = Counsellor(user_id=u.id, specialization=spec)
            db.session.add(c)
            counsellors.append(c)
        else:
            counsellors.append(u.counsellor_profile)

    db.session.flush()

    # 4. Approximately 100 Fictional Student Profiles
    print(f"Seeding {len(STUDENT_NAMES)} synthetic student records with multi-week telemetry...")
    random.seed(42) # Reproducible, deterministic distribution

    students = []
    today = date.today()

    predictor = DropoutPredictor()

    for i, full_name in enumerate(STUDENT_NAMES, start=1):
        email = f"student{i}@school.edu"
        user = User.query.filter_by(email=email).first()
        if user and user.student_profile:
            students.append(user.student_profile)
            continue

        if not user:
            user = User(name=full_name, email=email, role='student')
            user.set_password('student123')
            db.session.add(user)
            db.session.flush()

        dept = DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
        semester = ((i - 1) % 8) + 1
        enrollment_year = today.year - max(0, (semester - 1) // 2)

        # Structure distinct cohort archetypes across the 100 students:
        # i <= 15: Critical Review Cohort (Low attendance, low GPA, backlogs)
        # 16 <= i <= 28: Declining Attendance Trajectory (Steep drop in recent weeks)
        # 29 <= i <= 36: Recovering Attendance Cohort (Past low, recently improved)
        # 37 <= i <= 60: Moderate Risk / Borderline Cohort (65-74% attendance, 4.5-6.2 GPA)
        # 61 <= i <= 100: Stable / Satisfactory Progress (80-98% attendance, 7.0-9.8 GPA)

        if i <= 15:
            cohort_type = 'critical'
            base_gpa = random.uniform(2.3, 4.2)
            target_att = random.uniform(42.0, 62.0)
        elif i <= 28:
            cohort_type = 'declining'
            base_gpa = random.uniform(4.5, 6.0)
            target_att = random.uniform(55.0, 68.0)
        elif i <= 36:
            cohort_type = 'recovering'
            base_gpa = random.uniform(5.0, 6.8)
            target_att = random.uniform(72.0, 82.0)
        elif i <= 60:
            cohort_type = 'moderate'
            base_gpa = random.uniform(4.8, 6.4)
            target_att = random.uniform(66.0, 74.5)
        else:
            cohort_type = 'stable'
            base_gpa = random.uniform(7.2, 9.6)
            target_att = random.uniform(82.0, 97.0)

        student = Student(
            user_id=user.id,
            department=dept,
            semester=semester,
            enrollment_year=enrollment_year,
            attendance_pct=round(target_att, 1),
            gpa=round(base_gpa, 2),
            contact_phone=f"555-{1000 + i:04d}"
        )
        db.session.add(student)
        db.session.flush()
        students.append(student)

        # 5. Generate Department-Specific Subject Marks (Semester, Internal, Assignment)
        subjects = DEPARTMENT_SUBJECTS.get(dept, DEPARTMENT_SUBJECTS['Computer Science'])
        for sub in subjects:
            score_base = (base_gpa / 10.0) * 100.0

            if cohort_type == 'critical' and random.random() < 0.6:
                # Deliberate course backlog (score < 40)
                sem_score = round(random.uniform(25.0, 39.0), 1)
                int_score = round(random.uniform(30.0, 48.0), 1)
                assign_score = round(random.uniform(35.0, 52.0), 1)
            else:
                sem_score = round(max(0, min(100, score_base + random.uniform(-12, 12))), 1)
                int_score = round(max(0, min(100, score_base + random.uniform(-10, 10))), 1)
                assign_score = round(max(0, min(100, score_base + random.uniform(-6, 16))), 1)

            db.session.add(Marks(
                student_id=student.id, subject=sub, exam_type='semester',
                score=sem_score, max_score=100.0, semester=semester
            ))
            db.session.add(Marks(
                student_id=student.id, subject=sub, exam_type='internal',
                score=int_score, max_score=100.0, semester=semester
            ))
            db.session.add(Marks(
                student_id=student.id, subject=sub, exam_type='assignment',
                score=assign_score, max_score=100.0, semester=semester
            ))

        # 6. Generate 35-45 Daily Attendance Records Over the Past 50 Days (Historical Telemetry)
        att_days = 40
        present_count = 0.0
        total_days = 0

        for d in range(att_days, -1, -1):
            rec_date = today - timedelta(days=d)
            if rec_date.weekday() >= 5: # Skip weekends
                continue

            total_days += 1
            # Trend trajectory simulation
            if cohort_type == 'declining':
                # Started strong (85% present), plummeted in recent half (30% present)
                day_prob = 0.88 if d > (att_days // 2) else 0.32
            elif cohort_type == 'recovering':
                # Started poor (45% present), improved in recent half (88% present)
                day_prob = 0.45 if d > (att_days // 2) else 0.88
            elif cohort_type == 'critical':
                day_prob = target_att / 100.0
            elif cohort_type == 'moderate':
                day_prob = target_att / 100.0
            else:
                day_prob = target_att / 100.0

            r = random.random()
            if r < day_prob:
                status = 'present'
                present_count += 1.0
            elif r < day_prob + 0.12:
                status = 'late'
                present_count += 0.5
            else:
                status = 'absent'

            db.session.add(Attendance(
                student_id=student.id,
                date=rec_date,
                subject=random.choice(subjects),
                status=status
            ))

        # Synchronize exact attendance percentage with generated history
        if total_days > 0:
            student.attendance_pct = round((present_count / total_days) * 100.0, 1)

        # 7. Execute Predictor & Record Early-Warning Assessment
        db.session.flush()
        assessment_data = predictor.predict_risk(student.id)
        ra = RiskAssessment(
            student_id=student.id,
            risk_score=assessment_data.get('risk_score', 20),
            risk_level=assessment_data.get('risk_level', 'low'),
            contributing_factors="; ".join(assessment_data.get('contributing_factors', [])),
            assessment_source=assessment_data.get('assessment_source', 'Rule-Based Early-Warning Engine (Demo Policy Rules)'),
            assessed_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        db.session.add(ra)

        # 8. Initial Recommendations for High/Medium Students
        if assessment_data.get('risk_level') in ['high', 'medium']:
            recs = predictor.get_recommendations(
                assessment_data.get('risk_level'),
                assessment_data.get('contributing_factors', [])
            )
            for r_text in recs[:2]:
                db.session.add(Recommendation(
                    student_id=student.id,
                    type='study_plan' if 'tutor' in r_text.lower() else 'attendance_reminder',
                    content=r_text,
                    acknowledged=(random.random() < 0.3)
                ))

    # 9. Seed Active & Completed Interventions for ~28 Flagged Students
    print("Seeding initial intervention records across triage states...")
    support_catalog = [
        ('Attendance Barrier Review', 'Addressed morning transit and family commute difficulties. Provided institutional transit guidance.'),
        ('Academic Mentoring', 'Connected with department tutor for prerequisite math and algorithmic problem solving.'),
        ('Study Skills Coaching', 'Constructed a 25-minute Pomodoro study routine to balance internal exam preparation.'),
        ('Financial Aid Guidance', 'Assisted with institutional fee instalment application through student welfare cell.'),
        ('Wellness / Stress Support', 'Confidential check-in addressing test anxiety and coursework overwhelm.')
    ]

    flagged_students = [s for s in students if (s.latest_risk_level in ['High', 'Medium'])][:28]
    for idx, s in enumerate(flagged_students):
        c = counsellors[idx % len(counsellors)]
        stype, default_notes = support_catalog[idx % len(support_catalog)]

        if idx < 10:
            status = 'scheduled'
            sched_at = datetime.utcnow() + timedelta(days=random.randint(1, 6), hours=random.randint(1, 4))
            follow_date = (sched_at + timedelta(days=14)).date()
            outcome = ""
            notes = f"Scheduled follow-up meeting: {default_notes}"
        elif idx < 18:
            status = 'in_progress'
            sched_at = datetime.utcnow() - timedelta(days=random.randint(2, 7))
            follow_date = (sched_at + timedelta(days=10)).date()
            outcome = "Initial mentor diagnostic completed. Student engaged with remedial coaching resources."
            notes = f"Case open: {default_notes}"
        else:
            status = 'completed'
            sched_at = datetime.utcnow() - timedelta(days=random.randint(8, 20))
            follow_date = None
            outcome = "Barrier successfully addressed. Attendance and internal quiz marks demonstrated positive rebound."
            notes = f"Case resolved: {default_notes}"

        db.session.add(CounsellingSession(
            student_id=s.id,
            counsellor_id=c.id,
            mentor_name=c.user.name,
            support_type=stype,
            scheduled_at=sched_at,
            next_followup_date=follow_date,
            status=status,
            session_type='individual',
            notes=notes,
            outcome=outcome
        ))

    # 10. Seed Realistic Teacher Classroom Observations
    print("Seeding faculty observations...")
    obs_templates = [
        ('academic', 'Demonstrated active participation during engineering laboratory session.'),
        ('attendance', 'Missed consecutive morning lectures. Student indicated transportation delays.'),
        ('behavioral', 'Appears engaged in group discussions but hesitated during problem-solving assignments.'),
        ('personal', 'Requested brief advisory regarding balancing part-time family responsibilities with coursework.')
    ]
    for s in students[:24]:
        t = teachers[s.id % len(teachers)]
        cat, content = obs_templates[s.id % len(obs_templates)]
        db.session.add(Observation(
            student_id=s.id,
            teacher_id=t.id,
            category=cat,
            content=content,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 14))
        ))

    db.session.commit()
    print("Demonstration synthetic database seeded successfully!")
    print(f" -> Total Users: {User.query.count()}")
    print(f" -> Total Students: {Student.query.count()}")
    print(f" -> Total Attendance Records: {Attendance.query.count()}")
    print(f" -> Total Marks Records: {Marks.query.count()}")
    print(f" -> Total Assessments: {RiskAssessment.query.count()}")
    print(f" -> Total Counselling Sessions: {CounsellingSession.query.count()}")
    print(f" -> Total Observations: {Observation.query.count()}")

def ensure_seed_data(app=None, force=False):
    """
    Idempotent loader for application startup:
    Populates synthetic demonstration data if database is empty or missing students.
    """
    admin_exists = User.query.filter_by(role='admin').first() is not None
    student_count = Student.query.count()

    if not force and admin_exists and student_count >= 95:
        return

    print("Populating initial baseline synthetic demonstration dataset...")
    seed_db(force_recreate=force)

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_db(force_recreate=True)
