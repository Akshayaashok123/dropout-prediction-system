from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Student, Teacher, Counsellor

auth = Blueprint('auth', __name__)

def redirect_based_on_role(role):
    """Helper to redirect users to their respective dashboards."""
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    elif role == 'counsellor':
        return redirect(url_for('counsellor.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect_based_on_role(user.role)
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student') # Default to student
        name = request.form.get('name')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Create user
        new_user = User(
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            name=name
        )
        db.session.add(new_user)
        db.session.flush() # Get new_user.id
        
        # Create specific profile record based on role
        if role == 'student':
            student = Student(user_id=new_user.id)
            db.session.add(student)
        elif role == 'teacher':
            teacher = Teacher(user_id=new_user.id)
            db.session.add(teacher)
        elif role == 'counsellor':
            counsellor = Counsellor(user_id=new_user.id)
            db.session.add(counsellor)
            
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
