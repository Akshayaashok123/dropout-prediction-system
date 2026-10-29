from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False) # admin, teacher, counsellor, student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships setup in child models or below
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    enrollment_year = db.Column(db.Integer)
    attendance_pct = db.Column(db.Float)
    gpa = db.Column(db.Float)
    contact_phone = db.Column(db.String(20))
    
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    
    @property
    def name(self):
        return self.user.name if self.user else f'Student #{self.id}'

    @name.setter
    def name(self, val):
        if self.user:
            self.user.name = val

    @property
    def email(self):
        return self.user.email if self.user else ''

    @email.setter
    def email(self, val):
        if self.user:
            self.user.email = val

    @property
    def latest_assessment(self):
        return self.risk_assessments.order_by(RiskAssessment.assessed_at.desc()).first()

    @property
    def latest_risk_level(self):
        la = self.latest_assessment
        return la.risk_level.capitalize() if la and la.risk_level else 'Low'

    @latest_risk_level.setter
    def latest_risk_level(self, val):
        pass

    @property
    def latest_risk_score(self):
        la = self.latest_assessment
        return round(la.risk_score, 1) if la and la.risk_score is not None else 0.0

    @latest_risk_score.setter
    def latest_risk_score(self, val):
        pass

    @property
    def risk_level(self):
        return self.latest_risk_level

    @risk_level.setter
    def risk_level(self, val):
        pass

    @property
    def risk_score(self):
        return self.latest_risk_score

    @risk_score.setter
    def risk_score(self, val):
        pass

    @property
    def attendance(self):
        return round(self.attendance_pct or 0.0, 1)

    @attendance.setter
    def attendance(self, val):
        self.attendance_pct = val

    @property
    def latest_intervention(self):
        return self.counselling_sessions.order_by(CounsellingSession.scheduled_at.desc()).first()

    def __repr__(self):
        return f'<Student {self.user.name if self.user else self.id}>'

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department = db.Column(db.String(50))

    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))

    def __repr__(self):
        return f'<Teacher {self.user.name if self.user else self.id}>'

class Counsellor(db.Model):
    __tablename__ = 'counsellors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization = db.Column(db.String(100))

    user = db.relationship('User', backref=db.backref('counsellor_profile', uselist=False))

    def __repr__(self):
        return f'<Counsellor {self.user.name if self.user else self.id}>'

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    subject = db.Column(db.String(100))
    status = db.Column(db.String(20)) # present, absent, late

    student = db.relationship('Student', backref=db.backref('attendance_records', lazy='dynamic'))

class Marks(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(100))
    exam_type = db.Column(db.String(50)) # internal, semester, assignment
    score = db.Column(db.Float)
    max_score = db.Column(db.Float)
    semester = db.Column(db.Integer)

    student = db.relationship('Student', backref=db.backref('marks_records', lazy='dynamic'))

class RiskAssessment(db.Model):
    __tablename__ = 'risk_assessments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    risk_score = db.Column(db.Float) # 0-100
    risk_level = db.Column(db.String(20)) # low, medium, high
    contributing_factors = db.Column(db.Text) # JSON or structured string
    assessment_source = db.Column(db.String(100), default='Random Forest Model + Rule Engine')
    assessed_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref=db.backref('risk_assessments', lazy='dynamic'))

class CounsellingSession(db.Model):
    __tablename__ = 'counselling_sessions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    counsellor_id = db.Column(db.Integer, db.ForeignKey('counsellors.id'), nullable=True)
    mentor_name = db.Column(db.String(100), nullable=True)
    support_type = db.Column(db.String(100), default='Academic Mentoring') # Academic Mentoring, Attendance Support, Financial Aid Counseling, Wellness / Stress Check-in, Career Guidance
    scheduled_at = db.Column(db.DateTime, nullable=False)
    next_followup_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='scheduled') # scheduled, in_progress, completed, cancelled, no-show
    session_type = db.Column(db.String(50), default='individual') # individual, group
    notes = db.Column(db.Text) # private notes
    outcome = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref=db.backref('counselling_sessions', lazy='dynamic'))
    counsellor = db.relationship('Counsellor', backref=db.backref('sessions', lazy='dynamic'))

class Observation(db.Model):
    __tablename__ = 'observations'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50)) # academic, behavioral, attendance, personal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('Teacher', backref=db.backref('observations_made', lazy='dynamic'))
    student = db.relationship('Student', backref=db.backref('observations_received', lazy='dynamic'))

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    type = db.Column(db.String(50)) # study_plan, attendance_reminder, motivation, counsellor_referral
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)

    student = db.relationship('Student', backref=db.backref('recommendations', lazy='dynamic'))

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50)) # alert, info, warning
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
