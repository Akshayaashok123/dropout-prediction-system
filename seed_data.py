import os
import random
from datetime import datetime, timedelta
from app import create_app
from models import (db, User, Student, Teacher, Counsellor, Attendance, 
                   Marks, RiskAssessment, CounsellingSession, Observation,
                   Recommendation, Notification)

app = create_app()

DEPARTMENTS = ['Computer Science', 'Electronics & Comm.', 'Mechanical', 'Civil', 'Electrical']

def seed_db():
    with app.app_context():
        print("Dropping and recreating tables...")
        db.drop_all()
        db.create_all()

        print("Seeding Admin...")
        admin = User(name='System Admin', email='admin@school.edu', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        print("Seeding Teachers...")
        teachers = []
        for i in range(1, 4):
            user = User(name=f'Teacher {i}', email=f'teacher{i}@school.edu', role='teacher')
            user.set_password('teacher123')
            db.session.add(user)
            db.session.flush() # Get user id
            
            teacher = Teacher(user_id=user.id, department=random.choice(DEPARTMENTS))
            db.session.add(teacher)
            teachers.append(teacher)

        print("Seeding Counsellors...")
        counsellors = []
        for i in range(1, 3):
            user = User(name=f'Counsellor {i}', email=f'counsellor{i}@school.edu', role='counsellor')
            user.set_password('counsellor123')
            db.session.add(user)
            db.session.flush()
            
            counsellor = Counsellor(user_id=user.id, specialization='Academic Stress')
            db.session.add(counsellor)
            counsellors.append(counsellor)

        print("Seeding 50 Students...")
        students = []
        for i in range(1, 51):
            # Create user account
            user = User(name=f'Student {i}', email=f'student{i}@school.edu', role='student')
            user.set_password('student123')
            db.session.add(user)
            db.session.flush()
            
            # Determine risk profile (20% high risk, 30% medium, 50% low)
            rand = random.random()
            if rand < 0.20:
                attendance = random.uniform(40, 65)
                gpa = random.uniform(2.0, 5.0)
                risk_level = 'high'
                risk_score = random.uniform(70, 95)
            elif rand < 0.50:
                attendance = random.uniform(65, 80)
                gpa = random.uniform(5.0, 7.5)
                risk_level = 'medium'
                risk_score = random.uniform(40, 69)
            else:
                attendance = random.uniform(80, 98)
                gpa = random.uniform(7.5, 9.5)
                risk_level = 'low'
                risk_score = random.uniform(5, 39)
                
            student = Student(
                user_id=user.id,
                department=random.choice(DEPARTMENTS),
                semester=random.randint(1, 8),
                enrollment_year=datetime.now().year - random.randint(0, 3),
                attendance_pct=round(attendance, 2),
                gpa=round(gpa, 2),
                contact_phone=f"555-{random.randint(1000, 9999)}"
            )
            db.session.add(student)
            db.session.flush()
            students.append(student)
            
            # Add Risk Assessment
            assessment = RiskAssessment(
                student_id=student.id,
                risk_score=round(risk_score, 2),
                risk_level=risk_level,
                contributing_factors='{"attendance": "low", "grades": "declining"}' if risk_level == 'high' else '{}'
            )
            db.session.add(assessment)

            # Add Marks
            subjects = ['Math', 'Physics', 'Programming', 'Database', 'Networks']
            for sub in subjects:
                # Add marks proportional to GPA
                score_pct = gpa / 10.0 * 100
                
                # Semester marks
                actual_score = max(0, min(100, score_pct + random.uniform(-15, 15)))
                db.session.add(Marks(
                    student_id=student.id, subject=sub, exam_type='semester',
                    score=round(actual_score, 1), max_score=100.0, semester=student.semester
                ))
                
                # Internal marks
                internal_score = max(0, min(100, score_pct + random.uniform(-10, 10)))
                db.session.add(Marks(
                    student_id=student.id, subject=sub, exam_type='internal',
                    score=round(internal_score, 1), max_score=100.0, semester=student.semester
                ))
                
                # Assignment marks
                assign_score = max(0, min(100, score_pct + random.uniform(-5, 20)))
                db.session.add(Marks(
                    student_id=student.id, subject=sub, exam_type='assignment',
                    score=round(assign_score, 1), max_score=100.0, semester=student.semester
                ))
                
            # Add Attendance records for last 30 days
            today = datetime.now().date()
            for d in range(30):
                if random.random() > 0.3: # exclude some days (weekends etc)
                    record_date = today - timedelta(days=d)
                    status = 'present'
                    if random.random() * 100 > attendance:
                        status = 'absent' if random.random() > 0.3 else 'late'
                        
                    att = Attendance(
                        student_id=student.id,
                        date=record_date,
                        subject=random.choice(subjects),
                        status=status
                    )
                    db.session.add(att)

        print("Seeding Initial Intervention Records...")
        support_types = [
            'Academic Mentoring',
            'Attendance Barrier Review',
            'Financial Aid Guidance',
            'Wellness / Stress Support',
            'Study Skills Coaching'
        ]
        
        for idx, student in enumerate(students[:18]):
            c = counsellors[idx % len(counsellors)]
            status = 'scheduled' if idx < 7 else ('in_progress' if idx < 13 else 'completed')
            scheduled_date = datetime.utcnow() + timedelta(days=random.randint(-14, 7))
            next_followup = (scheduled_date + timedelta(days=14)).date() if status != 'completed' else None
            
            outcome = "Student agreed to join weekly remedial math study group and reported improved routine." if status == 'completed' else (
                "Initial check-in completed. Connected student with student affairs for fee scholarship." if status == 'in_progress' else ""
            )
            notes = f"Mentorship discussion addressing {random.choice(['lecture attendance barriers', 'internal assessment marks', 'time-management and exam anxiety', 'curriculum prerequisites'])}."
            
            sess = CounsellingSession(
                student_id=student.id,
                counsellor_id=c.id,
                mentor_name=c.user.name,
                support_type=random.choice(support_types),
                scheduled_at=scheduled_date,
                next_followup_date=next_followup,
                status=status,
                session_type='individual',
                notes=notes,
                outcome=outcome
            )
            db.session.add(sess)

        db.session.commit()
        print("Database seeded successfully!")
        
        print("\nSummary:")
        print(f"Users: {User.query.count()}")
        print(f"Students: {Student.query.count()}")
        print(f"Teachers: {Teacher.query.count()}")
        print(f"Counsellors: {Counsellor.query.count()}")
        print(f"Attendance Records: {Attendance.query.count()}")
        print(f"Marks Records: {Marks.query.count()}")
        print(f"Risk Assessments: {RiskAssessment.query.count()}")
        print(f"Interventions / Sessions: {CounsellingSession.query.count()}")

if __name__ == '__main__':
    seed_db()
