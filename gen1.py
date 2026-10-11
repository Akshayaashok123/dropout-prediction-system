import os

base_dir = r"C:\Users\Archana Ashok\.gemini\antigravity\scratch\dropout-prediction-system\templates"
os.makedirs(base_dir, exist_ok=True)
for d in ["auth", "admin", "teacher", "counsellor", "student", "errors"]:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

def w(path, content):
    with open(os.path.join(base_dir, path), "w", encoding="utf-8") as f:
        f.write(content.strip())

w("base.html", """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}EduGuard{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary-color: #1a237e;
            --sidebar-width: 250px;
        }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; }
        
        /* Navbar */
        .navbar { background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); position: fixed; width: 100%; z-index: 1001; top: 0;}
        .navbar-brand { color: var(--primary-color) !important; font-weight: bold; }
        
        /* Sidebar */
        .sidebar { height: 100vh; width: var(--sidebar-width); position: fixed; top: 0; left: 0; background-color: var(--primary-color); padding-top: 70px; color: white; z-index: 1000; transition: transform 0.3s ease;}
        .sidebar a { padding: 15px 20px; text-decoration: none; font-size: 16px; color: #cfd8dc; display: block; transition: 0.3s; }
        .sidebar a:hover { color: white; background-color: rgba(255,255,255,0.1); }
        .sidebar .active { background-color: rgba(255,255,255,0.2); color: white; font-weight: bold; border-left: 4px solid white;}
        
        /* Main Content */
        .main-content { margin-left: var(--sidebar-width); padding: 20px; padding-top: 80px; min-height: 100vh; transition: margin-left 0.3s ease;}
        
        /* Cards & Badges */
        .card { border: none; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
        .badge-low { background-color: #4caf50; color: white; }
        .badge-medium { background-color: #ff9800; color: white; }
        .badge-high { background-color: #f44336; color: white; }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; }
        ::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }
        
        /* Mobile Responsive */
        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); }
            .sidebar.show { transform: translateX(0); }
            .main-content { margin-left: 0; }
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-light">
        <div class="container-fluid">
            {% if current_user.is_authenticated %}
            <button class="btn border-0 d-md-none me-2" id="sidebarToggle">
                <i class="fas fa-bars"></i>
            </button>
            {% endif %}
            <a class="navbar-brand ms-2" href="/">🎓 EduGuard</a>
            <div class="d-flex align-items-center ms-auto">
                {% if current_user.is_authenticated %}
                <span class="me-3 fw-semibold text-muted">{{ current_user.name }} ({{ current_user.role }})</span>
                <a href="{{ url_for('auth.logout') }}" class="btn btn-outline-danger btn-sm">Logout</a>
                {% else %}
                <a href="{{ url_for('auth.login') }}" class="btn btn-outline-primary btn-sm me-2">Login</a>
                <a href="{{ url_for('auth.register') }}" class="btn btn-primary btn-sm" style="background-color: var(--primary-color);">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>

    {% if current_user.is_authenticated %}
    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        {% if current_user.role == 'Admin' %}
            <a href="{{ url_for('admin.dashboard') }}"><i class="fas fa-tachometer-alt me-2"></i>Dashboard</a>
            <a href="{{ url_for('admin.students') }}"><i class="fas fa-user-graduate me-2"></i>Students</a>
            <a href="{{ url_for('admin.users') }}"><i class="fas fa-users me-2"></i>Users</a>
            <a href="{{ url_for('admin.analytics') }}"><i class="fas fa-chart-pie me-2"></i>Analytics</a>
        {% elif current_user.role == 'Teacher' %}
            <a href="{{ url_for('teacher.dashboard') }}"><i class="fas fa-tachometer-alt me-2"></i>Dashboard</a>
            <a href="{{ url_for('teacher.students') }}"><i class="fas fa-users me-2"></i>My Students</a>
            <a href="{{ url_for('teacher.alerts') }}"><i class="fas fa-bell me-2"></i>Alerts</a>
        {% elif current_user.role == 'Counsellor' %}
            <a href="{{ url_for('counsellor.dashboard') }}"><i class="fas fa-tachometer-alt me-2"></i>Dashboard</a>
            <a href="{{ url_for('counsellor.referrals') }}"><i class="fas fa-user-injured me-2"></i>Referrals</a>
            <a href="{{ url_for('counsellor.sessions') }}"><i class="fas fa-comments me-2"></i>Sessions</a>
        {% elif current_user.role == 'Student' %}
            <a href="{{ url_for('student.dashboard') }}"><i class="fas fa-home me-2"></i>Dashboard</a>
            <a href="{{ url_for('student.recommendations') }}"><i class="fas fa-star me-2"></i>Recommendations</a>
            <a href="{{ url_for('student.resources') }}"><i class="fas fa-book me-2"></i>Resources</a>
            <a href="{{ url_for('student.sessions') }}"><i class="fas fa-calendar-alt me-2"></i>My Sessions</a>
            <a href="{{ url_for('student.request_help') }}"><i class="fas fa-hands-helping me-2"></i>Get Help</a>
        {% endif %}
    </div>
    {% endif %}

    <!-- Main Content -->
    <div class="{% if current_user.is_authenticated %}main-content{% else %}container mt-5 pt-5{% endif %}" id="mainContent">
        <div class="container-fluid">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }} alert-dismissible fade show shadow-sm" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            {% block content %}{% endblock %}
        </div>
    </div>

    <footer class="text-center mt-5 py-3 text-muted {% if current_user.is_authenticated %}ms-auto{% endif %}" style="{% if current_user.is_authenticated %}margin-left: var(--sidebar-width);{% endif %}">
        <small>&copy; 2023 EduGuard. All rights reserved.</small>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const sidebarToggle = document.getElementById('sidebarToggle');
        if(sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                document.getElementById('sidebar').classList.toggle('show');
            });
        }
    </script>
    {% block scripts %}{% endblock %}
</body>
</html>
""")

w("landing.html", """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EduGuard - AI-Powered Dropout Prediction</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { font-family: 'Segoe UI', sans-serif; overflow-x: hidden; }
        .navbar-brand { font-weight: bold; color: #1a237e !important; font-size: 1.5rem;}
        .hero { background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%); color: white; padding: 120px 0 100px; text-align: center; }
        .hero h1 { font-size: 3.5rem; font-weight: bold; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);}
        .hero p { font-size: 1.25rem; margin-bottom: 40px; opacity: 0.9; }
        .step-card { text-align: center; padding: 40px 20px; border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-radius: 12px; height: 100%; transition: transform 0.3s; background: white;}
        .step-card:hover { transform: translateY(-10px); box-shadow: 0 8px 25px rgba(0,0,0,0.1);}
        .step-icon { font-size: 45px; color: #1a237e; margin-bottom: 25px; }
        .stat-box { background: white; padding: 40px 20px; text-align: center; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);}
        .stat-box h2 { color: #1a237e; font-size: 2.8rem; font-weight: bold; margin-bottom: 10px;}
        .feature-card { border-left: 5px solid #1a237e; padding: 30px; background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; border-radius: 0 10px 10px 0;}
        footer { background: #0a1045; color: rgba(255,255,255,0.8); padding: 50px 0 20px; text-align: center; }
        footer a { color: rgba(255,255,255,0.8); text-decoration: none; }
        footer a:hover { color: white; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm py-3 fixed-top">
        <div class="container">
            <a class="navbar-brand" href="#">🎓 EduGuard</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <div class="ms-auto">
                    <a href="{{ url_for('auth.login') }}" class="btn btn-outline-primary me-2 px-4">Login</a>
                    <a href="{{ url_for('auth.register') }}" class="btn btn-primary px-4" style="background-color: #1a237e; border-color: #1a237e;">Get Started</a>
                </div>
            </div>
        </div>
    </nav>

    <section class="hero mt-5">
        <div class="container">
            <h1>EduGuard</h1>
            <p>AI-Powered Dropout Prediction & Counselling System</p>
            <a href="{{ url_for('auth.login') }}" class="btn btn-light btn-lg text-primary px-5 py-3 fw-bold rounded-pill shadow-lg mt-3">Login to Dashboard <i class="fas fa-arrow-right ms-2"></i></a>
        </div>
    </section>

    <section class="py-5 bg-light">
        <div class="container py-5">
            <h2 class="text-center mb-5" style="color: #1a237e; font-weight: bold;">How It Works</h2>
            <div class="row g-4">
                <div class="col-md-3">
                    <div class="step-card">
                        <i class="fas fa-database step-icon"></i>
                        <h5>1. Data Collection</h5>
                        <p class="text-muted small mt-3">Gathering attendance, grades, and engagement metrics securely.</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="step-card">
                        <i class="fas fa-brain step-icon"></i>
                        <h5>2. AI Analysis</h5>
                        <p class="text-muted small mt-3">Machine learning algorithms process data to identify risk patterns.</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="step-card">
                        <i class="fas fa-chart-pie step-icon"></i>
                        <h5>3. Risk Assessment</h5>
                        <p class="text-muted small mt-3">Students are categorized into clear, actionable risk levels.</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="step-card">
                        <i class="fas fa-hands-helping step-icon"></i>
                        <h5>4. Counselling Support</h5>
                        <p class="text-muted small mt-3">Timely interventions and personalized help are provided.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="py-5">
        <div class="container py-5">
            <div class="row text-center g-4">
                <div class="col-md-3"><div class="stat-box"><h2>50+</h2><p class="mb-0 text-muted fw-semibold">Students Monitored</p></div></div>
                <div class="col-md-3"><div class="stat-box"><h2>3</h2><p class="mb-0 text-muted fw-semibold">Risk Levels</p></div></div>
                <div class="col-md-3"><div class="stat-box"><h2><i class="fas fa-bolt text-warning"></i></h2><p class="mb-0 text-muted fw-semibold">Real-time Alerts</p></div></div>
                <div class="col-md-3"><div class="stat-box"><h2><i class="fas fa-robot text-primary"></i></h2><p class="mb-0 text-muted fw-semibold">AI Recommendations</p></div></div>
            </div>
        </div>
    </section>

    <section class="py-5 bg-light">
        <div class="container py-5">
            <h2 class="text-center mb-5" style="color: #1a237e; font-weight: bold;">Key Features</h2>
            <div class="row">
                <div class="col-lg-4">
                    <div class="feature-card">
                        <h4 style="color: #1a237e;"><i class="fas fa-bell text-warning me-2"></i> Early Warning System</h4>
                        <p class="text-muted mt-3 mb-0">Detect subtle signs of academic struggle before they become major issues. Intervene early to ensure student success.</p>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="feature-card">
                        <h4 style="color: #1a237e;"><i class="fas fa-user-md text-success me-2"></i> Personalized Support</h4>
                        <p class="text-muted mt-3 mb-0">Tailored AI-driven recommendations and direct links to professional counselling for every student in need.</p>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="feature-card">
                        <h4 style="color: #1a237e;"><i class="fas fa-shield-alt text-primary me-2"></i> Privacy First</h4>
                        <p class="text-muted mt-3 mb-0">Non-stigmatizing interface for students and secure data handling. We show 'Wellness Scores', not 'Dropout Risk'.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <footer>
        <div class="container">
            <h4 class="mb-4 text-white">🎓 EduGuard</h4>
            <div class="d-flex justify-content-center gap-4 mb-4">
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
                <a href="#">Contact Support</a>
            </div>
            <p class="mb-0 small">&copy; 2023 EduGuard. All rights reserved.</p>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
""")

w("auth/login.html", """
{% extends 'base.html' %}
{% block title %}Login - EduGuard{% endblock %}
{% block content %}
<div class="row justify-content-center align-items-center" style="min-height: 70vh;">
    <div class="col-md-5 col-lg-4">
        <div class="card shadow-lg border-0">
            <div class="card-body p-5">
                <div class="text-center mb-4">
                    <i class="fas fa-user-circle fa-4x mb-3" style="color: var(--primary-color);"></i>
                    <h3 class="fw-bold" style="color: var(--primary-color);">Welcome Back</h3>
                    <p class="text-muted">Please login to your account</p>
                </div>
                <form method="POST" action="">
                    <div class="mb-4">
                        <label class="form-label fw-semibold">Email address</label>
                        <div class="input-group">
                            <span class="input-group-text bg-light border-end-0"><i class="fas fa-envelope text-muted"></i></span>
                            <input type="email" class="form-control border-start-0 bg-light" name="email" required placeholder="name@example.com">
                        </div>
                    </div>
                    <div class="mb-4">
                        <label class="form-label fw-semibold">Password</label>
                        <div class="input-group">
                            <span class="input-group-text bg-light border-end-0"><i class="fas fa-lock text-muted"></i></span>
                            <input type="password" class="form-control border-start-0 bg-light" name="password" required placeholder="Enter password">
                        </div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input" name="remember" id="remember">
                            <label class="form-check-label text-muted" for="remember">Remember me</label>
                        </div>
                        <a href="#" class="text-decoration-none small" style="color: var(--primary-color);">Forgot Password?</a>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 py-2 fw-bold" style="background-color: var(--primary-color); border: none;">Login</button>
                </form>
                <div class="text-center mt-4">
                    <p class="mb-0 text-muted">Don't have an account? <a href="{{ url_for('auth.register') }}" class="fw-bold text-decoration-none" style="color: var(--primary-color);">Register here</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""")

w("auth/register.html", """
{% extends 'base.html' %}
{% block title %}Register - EduGuard{% endblock %}
{% block content %}
<div class="row justify-content-center align-items-center" style="min-height: 70vh;">
    <div class="col-md-6 col-lg-5">
        <div class="card shadow-lg border-0 my-4">
            <div class="card-body p-5">
                <div class="text-center mb-4">
                    <i class="fas fa-user-plus fa-3x mb-3" style="color: var(--primary-color);"></i>
                    <h3 class="fw-bold" style="color: var(--primary-color);">Create Account</h3>
                    <p class="text-muted">Join EduGuard today</p>
                </div>
                <form method="POST" action="">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Full Name</label>
                        <input type="text" class="form-control bg-light" name="name" required placeholder="John Doe">
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Email address</label>
                        <input type="email" class="form-control bg-light" name="email" required placeholder="john@example.com">
                    </div>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label fw-semibold">Password</label>
                            <input type="password" class="form-control bg-light" name="password" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label fw-semibold">Confirm Password</label>
                            <input type="password" class="form-control bg-light" name="confirm_password" required>
                        </div>
                    </div>
                    <div class="mb-4">
                        <label class="form-label fw-semibold">Role</label>
                        <select class="form-select bg-light" name="role" required>
                            <option value="">Select a role...</option>
                            <option value="Student">Student</option>
                            <option value="Teacher">Teacher</option>
                            <option value="Counsellor">Counsellor</option>
                            <option value="Admin">Admin</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 py-2 fw-bold" style="background-color: var(--primary-color); border: none;">Register</button>
                </form>
                <div class="text-center mt-4">
                    <p class="mb-0 text-muted">Already have an account? <a href="{{ url_for('auth.login') }}" class="fw-bold text-decoration-none" style="color: var(--primary-color);">Login here</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""")

w("admin/dashboard.html", """
{% extends 'base.html' %}
{% block title %}Admin Dashboard - EduGuard{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 style="color: var(--primary-color);"><i class="fas fa-tachometer-alt me-2"></i>Admin Dashboard</h2>
    <form method="POST" action="{{ url_for('admin.run_prediction') }}">
        <button type="submit" class="btn btn-primary shadow-sm" style="background-color: var(--primary-color);"><i class="fas fa-brain me-2"></i>Run AI Prediction</button>
    </form>
</div>

<div class="row g-4 mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="text-uppercase mb-1">Total Students</h6>
                        <h2 class="mb-0 fw-bold">{{ stats.total_students|default(0) }}</h2>
                    </div>
                    <i class="fas fa-users fa-2x opacity-50"></i>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-danger text-white h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="text-uppercase mb-1">High Risk</h6>
                        <h2 class="mb-0 fw-bold">{{ stats.high_risk|default(0) }}</h2>
                    </div>
                    <i class="fas fa-exclamation-triangle fa-2x opacity-50"></i>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="text-uppercase mb-1">Medium Risk</h6>
                        <h2 class="mb-0 fw-bold">{{ stats.medium_risk|default(0) }}</h2>
                    </div>
                    <i class="fas fa-exclamation-circle fa-2x opacity-50"></i>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white h-100">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="text-uppercase mb-1">Low Risk</h6>
                        <h2 class="mb-0 fw-bold">{{ stats.low_risk|default(0) }}</h2>
                    </div>
                    <i class="fas fa-check-circle fa-2x opacity-50"></i>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row g-4 mb-4">
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header bg-white fw-bold">Risk Distribution</div>
            <div class="card-body">
                <canvas id="riskChart"></canvas>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header bg-white fw-bold">Department-wise Risk</div>
            <div class="card-body">
                <canvas id="deptChart"></canvas>
            </div>
        </div>
    </div>
</div>

<div class="card mb-4">
    <div class="card-header bg-white fw-bold">
        Recent Risk Assessments
    </div>
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover mb-0 align-middle">
                <thead class="table-light">
                    <tr>
                        <th>Student Name</th>
                        <th>Department</th>
                        <th>Risk Score</th>
                        <th>Level</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    {% for assessment in recent_assessments %}
                    <tr>
                        <td>{{ assessment.student_name }}</td>
                        <td>{{ assessment.department }}</td>
                        <td>{{ assessment.risk_score }}</td>
                        <td>
                            <span class="badge {% if assessment.level == 'High' %}badge-high{% elif assessment.level == 'Medium' %}badge-medium{% else %}badge-low{% endif %}">
                                {{ assessment.level }}
                            </span>
                        </td>
                        <td>{{ assessment.date }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="5" class="text-center py-3 text-muted">No recent assessments found.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const riskCtx = document.getElementById('riskChart').getContext('2d');
        new Chart(riskCtx, {
            type: 'doughnut',
            data: {
                labels: ['High Risk', 'Medium Risk', 'Low Risk'],
                datasets: [{
                    data: [{{ stats.high_risk|default(1) }}, {{ stats.medium_risk|default(2) }}, {{ stats.low_risk|default(7) }}],
                    backgroundColor: ['#f44336', '#ff9800', '#4caf50'],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });

        const deptCtx = document.getElementById('deptChart').getContext('2d');
        new Chart(deptCtx, {
            type: 'bar',
            data: {
                labels: ['Computer Science', 'Engineering', 'Business', 'Arts'],
                datasets: [{
                    label: 'High Risk Students',
                    data: [5, 2, 3, 1],
                    backgroundColor: '#f44336'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    });
</script>
{% endblock %}
""")
