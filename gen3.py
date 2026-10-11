import os

base_dir = r"C:\Users\Archana Ashok\.gemini\antigravity\scratch\dropout-prediction-system\templates"

def w(path, content):
    with open(os.path.join(base_dir, path), "w", encoding="utf-8") as f:
        f.write(content.strip())

w("teacher/dashboard.html", """
{% extends 'base.html' %}
{% block title %}Teacher Dashboard - EduGuard{% endblock %}
{% block content %}
<h3 class="mb-4" style="color: var(--primary-color);">Welcome, {{ current_user.name|default('Teacher') }}</h3>

<div class="row g-4 mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white h-100">
            <div class="card-body">
                <h6 class="text-uppercase mb-1">Total Students</h6>
                <h2 class="mb-0 fw-bold">{{ stats.total|default(40) }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-danger text-white h-100">
            <div class="card-body">
                <h6 class="text-uppercase mb-1">At Risk</h6>
                <h2 class="mb-0 fw-bold">{{ stats.at_risk|default(3) }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white h-100">
            <div class="card-body">
                <h6 class="text-uppercase mb-1">Needs Attention</h6>
                <h2 class="mb-0 fw-bold">{{ stats.needs_attention|default(5) }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white h-100">
            <div class="card-body">
                <h6 class="text-uppercase mb-1">Stable</h6>
                <h2 class="mb-0 fw-bold">{{ stats.stable|default(32) }}</h2>
            </div>
        </div>
    </div>
</div>

<div class="row g-4">
    <div class="col-md-8">
        <div class="card mb-4 h-100">
            <div class="card-header bg-white fw-bold d-flex justify-content-between align-items-center">
                <span>Top 5 Highest Risk Students</span>
                <a href="{{ url_for('teacher.students') }}" class="btn btn-sm btn-outline-primary">View All</a>
            </div>
            <div class="card-body p-0">
                <ul class="list-group list-group-flush">
                    {% for student in top_risk_students|default([{'name':'John Doe', 'risk':'High', 'score':85}]) %}
                    <li class="list-group-item d-flex justify-content-between align-items-center py-3">
                        <div>
                            <h6 class="mb-0">{{ student.name }}</h6>
                            <small class="text-muted">Score: {{ student.score }}</small>
                        </div>
                        <span class="badge {% if student.risk == 'High' %}badge-high{% elif student.risk == 'Medium' %}badge-medium{% else %}badge-low{% endif %} rounded-pill">
                            {{ student.risk }}
                        </span>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card mb-4 h-100">
            <div class="card-header bg-white fw-bold">Recent Alerts</div>
            <div class="card-body p-0">
                <div class="list-group list-group-flush">
                    {% for alert in alerts|default([{'title':'Risk Increase', 'time':'2h ago'}]) %}
                    <a href="#" class="list-group-item list-group-item-action py-3">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1"><i class="fas fa-exclamation-circle text-warning me-2"></i>{{ alert.title }}</h6>
                            <small class="text-muted">{{ alert.time }}</small>
                        </div>
                        <p class="mb-1 small">Student risk level changed.</p>
                    </a>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""")

w("student/dashboard.html", """
{% extends 'base.html' %}
{% block title %}Student Dashboard - EduGuard{% endblock %}
{% block content %}
<h3 class="mb-4" style="color: var(--primary-color);">Welcome, {{ current_user.name|default('Student') }}</h3>

<div class="row g-4 mb-4 align-items-stretch">
    <div class="col-md-4">
        <div class="card h-100 text-center py-5 shadow-sm border-0">
            <div class="card-body d-flex flex-column justify-content-center align-items-center">
                <h5 class="text-muted mb-4">Your Wellness Score</h5>
                {% set score = 100 - (student.risk_score|default(20)) %}
                <div class="d-flex justify-content-center align-items-center rounded-circle text-white shadow" 
                    style="width: 150px; height: 150px; font-size: 3rem; font-weight: bold; background-color: {% if score >= 80 %}#4caf50{% elif score >= 50 %}#ff9800{% else %}#f44336{% endif %};">
                    {{ score }}
                </div>
                <p class="mt-4 text-muted small px-3">Your wellness score reflects your overall academic health. A higher score means you are on the right track!</p>
            </div>
        </div>
    </div>
    
    <div class="col-md-8">
        <div class="row g-4 h-100">
            <div class="col-md-6">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body text-center d-flex flex-column justify-content-center">
                        <i class="fas fa-calendar-check fa-3x text-primary mb-3"></i>
                        <h6 class="text-muted text-uppercase mb-2">Attendance %</h6>
                        <h2 class="fw-bold mb-0">{{ student.attendance|default(85) }}%</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body text-center d-flex flex-column justify-content-center">
                        <i class="fas fa-graduation-cap fa-3x text-success mb-3"></i>
                        <h6 class="text-muted text-uppercase mb-2">Current GPA</h6>
                        <h2 class="fw-bold mb-0">{{ student.gpa|default(3.2) }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-12 mt-4">
                <div class="card border-0 shadow-sm h-100">
                    <div class="card-body d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="mb-1 fw-bold text-primary">Upcoming Sessions</h5>
                            <p class="mb-0 text-muted small">You have {{ upcoming_sessions|default([])|length }} sessions scheduled.</p>
                        </div>
                        <a href="{{ url_for('student.sessions') }}" class="btn btn-primary" style="background-color: var(--primary-color);">View Schedule</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row g-4">
    <div class="col-12">
        <div class="card shadow-sm border-0">
            <div class="card-header bg-white border-0 pt-4 pb-0">
                <h5 class="fw-bold text-primary"><i class="fas fa-star text-warning me-2"></i>Recent Recommendations</h5>
            </div>
            <div class="card-body">
                <div class="list-group list-group-flush">
                    {% for rec in recommendations|default([{'type':'study_plan', 'content':'Review Chapter 4 before midterms.', 'date':'Today'}]) %}
                    <div class="list-group-item px-0 py-3 d-flex align-items-start border-bottom">
                        <div class="bg-light rounded p-3 me-3">
                            {% if rec.type == 'study_plan' %}<i class="fas fa-book text-primary"></i>
                            {% elif rec.type == 'attendance_reminder' %}<i class="fas fa-calendar text-warning"></i>
                            {% elif rec.type == 'motivation' %}<i class="fas fa-bolt text-success"></i>
                            {% else %}<i class="fas fa-user text-info"></i>{% endif %}
                        </div>
                        <div>
                            <p class="mb-1 fw-semibold">{{ rec.content }}</p>
                            <small class="text-muted">{{ rec.date }}</small>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""")

w("student/request_help.html", """
{% extends 'base.html' %}
{% block title %}Request Help - EduGuard{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card shadow-sm border-0 mt-4">
            <div class="card-body p-5">
                <div class="text-center mb-5">
                    <i class="fas fa-hands-helping fa-3x mb-3" style="color: var(--primary-color);"></i>
                    <h3 class="fw-bold" style="color: var(--primary-color);">Reach Out for Help</h3>
                    <p class="text-muted lead">It's okay to ask for help. We are here to support you.</p>
                </div>

                <form method="POST" action="">
                    <div class="mb-4">
                        <label class="form-label fw-bold text-muted">What do you need help with?</label>
                        <select class="form-select form-select-lg bg-light" name="category" required>
                            <option value="">Select a category...</option>
                            <option value="Academic">Academic Support</option>
                            <option value="Personal">Personal/Mental Health</option>
                            <option value="Financial">Financial Issues</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    
                    <div class="mb-4">
                        <label class="form-label fw-bold text-muted">Tell us more (Optional)</label>
                        <textarea class="form-control bg-light" name="message" rows="5" placeholder="Share as much or as little as you'd like..."></textarea>
                    </div>

                    <div class="mb-4 bg-light p-3 rounded">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="anonymous" id="anonymous">
                            <label class="form-check-label fw-semibold" for="anonymous">
                                Keep my request anonymous
                            </label>
                            <small class="d-block text-muted mt-1">If you check this, your counsellor will not know your identity unless you choose to share it later.</small>
                        </div>
                    </div>

                    <button type="submit" class="btn btn-primary btn-lg w-100 fw-bold" style="background-color: var(--primary-color); border: none;">Submit Request <i class="fas fa-paper-plane ms-2"></i></button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""")
