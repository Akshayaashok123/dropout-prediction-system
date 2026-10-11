import os

base_dir = r"C:\Users\Archana Ashok\.gemini\antigravity\scratch\dropout-prediction-system\templates"

def w(path, content):
    with open(os.path.join(base_dir, path), "w", encoding="utf-8") as f:
        f.write(content.strip())

w("admin/students.html", """
{% extends 'base.html' %}
{% block title %}Students - Admin - EduGuard{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h3 style="color: var(--primary-color);">Students Directory</h3>
    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#uploadModal" style="background-color: var(--primary-color);">
        <i class="fas fa-file-csv me-2"></i>Upload CSV
    </button>
</div>

<div class="card mb-4">
    <div class="card-body">
        <form class="row g-3">
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="Search by name or ID...">
            </div>
            <div class="col-md-3">
                <select class="form-select">
                    <option value="">All Departments</option>
                    <option value="CS">Computer Science</option>
                    <option value="ENG">Engineering</option>
                </select>
            </div>
            <div class="col-md-3">
                <select class="form-select">
                    <option value="">All Risk Levels</option>
                    <option value="High">High Risk</option>
                    <option value="Medium">Medium Risk</option>
                    <option value="Low">Low Risk</option>
                </select>
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-outline-primary w-100">Filter</button>
            </div>
        </form>
    </div>
</div>

<div class="card">
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover mb-0 align-middle">
                <thead class="table-light">
                    <tr>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Sem</th>
                        <th>Attendance</th>
                        <th>GPA</th>
                        <th>Risk Level</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in students %}
                    <tr>
                        <td>
                            <div class="d-flex align-items-center">
                                <div class="bg-light rounded-circle p-2 me-2"><i class="fas fa-user text-secondary"></i></div>
                                <div>
                                    <h6 class="mb-0">{{ student.name }}</h6>
                                    <small class="text-muted">{{ student.email }}</small>
                                </div>
                            </div>
                        </td>
                        <td>{{ student.department }}</td>
                        <td>{{ student.semester }}</td>
                        <td>
                            <div class="progress" style="height: 6px; width: 60px;">
                                <div class="progress-bar {% if student.attendance < 75 %}bg-danger{% else %}bg-success{% endif %}" role="progressbar" style="width: {{ student.attendance }}%;"></div>
                            </div>
                            <small>{{ student.attendance }}%</small>
                        </td>
                        <td>{{ student.gpa }}</td>
                        <td>
                            <span class="badge {% if student.risk_level == 'High' %}badge-high{% elif student.risk_level == 'Medium' %}badge-medium{% else %}badge-low{% endif %}">
                                {{ student.risk_level }}
                            </span>
                        </td>
                        <td>
                            <a href="{{ url_for('admin.student_detail', id=student.id) }}" class="btn btn-sm btn-outline-primary">View</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="7" class="text-center py-4 text-muted">No students found.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Upload Modal -->
<div class="modal fade" id="uploadModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Upload Students CSV</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <form method="POST" action="/admin/upload" enctype="multipart/form-data">
            <div class="mb-3">
                <label class="form-label">Select CSV File</label>
                <input class="form-control" type="file" name="file" accept=".csv" required>
            </div>
            <p class="small text-muted">CSV must contain headers: name, email, department, semester, attendance, gpa.</p>
            <button type="submit" class="btn btn-primary w-100" style="background-color: var(--primary-color);">Upload & Process</button>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

w("admin/student_detail.html", """
{% extends 'base.html' %}
{% block title %}Student Detail - EduGuard{% endblock %}
{% block content %}
<div class="mb-4">
    <a href="{{ url_for('admin.students') }}" class="text-decoration-none text-muted"><i class="fas fa-arrow-left me-2"></i>Back to Students</a>
</div>

<div class="row g-4">
    <!-- Profile & Risk -->
    <div class="col-md-4">
        <div class="card mb-4">
            <div class="card-body text-center py-4">
                <div class="bg-light rounded-circle d-inline-flex p-4 mb-3">
                    <i class="fas fa-user-graduate fa-4x text-secondary"></i>
                </div>
                <h4 class="fw-bold mb-1">{{ student.name|default("Student Name") }}</h4>
                <p class="text-muted mb-3">{{ student.email|default("student@example.com") }}</p>
                <div class="d-flex justify-content-center gap-2 mb-3">
                    <span class="badge bg-secondary">{{ student.department|default("CS") }}</span>
                    <span class="badge bg-secondary">Sem {{ student.semester|default("3") }}</span>
                    <span class="badge bg-secondary">{{ student.enrollment_year|default("2022") }}</span>
                </div>
            </div>
        </div>

        <div class="card border-0 shadow-sm">
            <div class="card-body text-center py-4">
                <h5 class="text-muted mb-3">Current Risk Status</h5>
                {% set risk = student.risk_level|default("Medium") %}
                <div class="d-inline-flex justify-content-center align-items-center rounded-circle mb-3 text-white 
                    {% if risk == 'High' %}badge-high{% elif risk == 'Medium' %}badge-medium{% else %}badge-low{% endif %}" 
                    style="width: 120px; height: 120px; font-size: 2rem; font-weight: bold;">
                    {{ student.risk_score|default(65) }}
                </div>
                <h4 class="fw-bold {% if risk == 'High' %}text-danger{% elif risk == 'Medium' %}text-warning{% else %}text-success{% endif %}">{{ risk }} Risk</h4>
            </div>
        </div>
    </div>

    <!-- Charts & Data -->
    <div class="col-md-8">
        <div class="row g-4 mb-4">
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header bg-white fw-bold">Attendance Trend (30 Days)</div>
                    <div class="card-body">
                        <canvas id="attendanceChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header bg-white fw-bold">Subject Marks</div>
                    <div class="card-body">
                        <canvas id="marksChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- History & Observations -->
        <div class="card mb-4">
            <div class="card-header bg-white fw-bold">Risk History</div>
            <div class="card-body">
                <div class="timeline position-relative ps-4 border-start border-2 border-primary">
                    {% for h in student.risk_history|default([{'date':'Oct 1', 'level':'Low'}, {'date':'Oct 5', 'level':'Medium'}]) %}
                    <div class="mb-3 position-relative">
                        <div class="position-absolute bg-primary rounded-circle" style="width: 12px; height: 12px; left: -27px; top: 5px;"></div>
                        <div class="text-muted small">{{ h.date }}</div>
                        <div class="fw-semibold">Changed to {{ h.level }} Risk</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <ul class="nav nav-tabs mb-3" id="studentTabs" role="tablist">
            <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#obs">Observations</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#sessions">Counselling</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#recs">Recommendations</button></li>
        </ul>
        <div class="tab-content card border-top-0 rounded-bottom">
            <div class="tab-pane fade show active p-3" id="obs">
                <p class="text-muted mb-0">Teacher observations go here.</p>
            </div>
            <div class="tab-pane fade p-3" id="sessions">
                <p class="text-muted mb-0">Counselling session history goes here.</p>
            </div>
            <div class="tab-pane fade p-3" id="recs">
                <p class="text-muted mb-0">AI recommendations applied go here.</p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const attCtx = document.getElementById('attendanceChart').getContext('2d');
        new Chart(attCtx, {
            type: 'line',
            data: {
                labels: ['W1', 'W2', 'W3', 'W4'],
                datasets: [{ label: 'Attendance %', data: [90, 85, 70, 60], borderColor: '#1a237e', tension: 0.3 }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });

        const marksCtx = document.getElementById('marksChart').getContext('2d');
        new Chart(marksCtx, {
            type: 'bar',
            data: {
                labels: ['Math', 'Physics', 'CS', 'English'],
                datasets: [{ label: 'Score', data: [65, 50, 85, 70], backgroundColor: '#4caf50' }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    });
</script>
{% endblock %}
""")

w("admin/analytics.html", """
{% extends 'base.html' %}
{% block title %}Analytics - EduGuard{% endblock %}
{% block content %}
<h3 class="mb-4" style="color: var(--primary-color);">System Analytics</h3>

<div class="row g-4 mb-4">
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header bg-white fw-bold">Overall Risk Distribution</div>
            <div class="card-body">
                <canvas id="distChart" style="min-height: 300px;"></canvas>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header bg-white fw-bold">Department-wise Risk</div>
            <div class="card-body">
                <canvas id="stackedChart" style="min-height: 300px;"></canvas>
            </div>
        </div>
    </div>
</div>

<div class="row g-4 mb-4">
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header bg-white fw-bold">Attendance vs GPA</div>
            <div class="card-body">
                <canvas id="scatterChart" style="min-height: 300px;"></canvas>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header bg-white fw-bold">Monthly Dropout Risk Trend</div>
            <div class="card-body">
                <canvas id="trendChart" style="min-height: 300px;"></canvas>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const chartData = {{ chart_data | default('null') | tojson }};
        // Setup empty placeholders if data is not passed
        new Chart(document.getElementById('distChart'), {
            type: 'doughnut',
            data: { labels: ['High', 'Medium', 'Low'], datasets: [{ data: [15, 30, 55], backgroundColor: ['#f44336', '#ff9800', '#4caf50'] }] }
        });
        new Chart(document.getElementById('stackedChart'), {
            type: 'bar',
            data: { labels: ['CS', 'ENG', 'BUS'], datasets: [{ label: 'High', data: [5, 10, 2], backgroundColor: '#f44336' }] },
            options: { scales: { x: { stacked: true }, y: { stacked: true } } }
        });
        new Chart(document.getElementById('scatterChart'), {
            type: 'scatter',
            data: { datasets: [{ label: 'Students', data: [{x: 60, y: 2.5}, {x: 80, y: 3.5}, {x: 95, y: 4.0}], backgroundColor: '#1a237e' }] },
            options: { scales: { x: { title: {display: true, text: 'Attendance %'} }, y: { title: {display: true, text: 'GPA'} } } }
        });
        new Chart(document.getElementById('trendChart'), {
            type: 'line',
            data: { labels: ['Jan', 'Feb', 'Mar', 'Apr'], datasets: [{ label: 'Avg Risk Score', data: [30, 35, 45, 40], borderColor: '#f44336', fill: true, backgroundColor: 'rgba(244,67,54,0.1)' }] }
        });
    });
</script>
{% endblock %}
""")

w("admin/users.html", """
{% extends 'base.html' %}
{% block title %}Users - Admin - EduGuard{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h3 style="color: var(--primary-color);">System Users</h3>
    <button class="btn btn-primary" style="background-color: var(--primary-color);"><i class="fas fa-plus me-2"></i>Add User</button>
</div>

<div class="card mb-4">
    <div class="card-body">
        <form class="row g-3">
            <div class="col-md-6">
                <input type="text" class="form-control" placeholder="Search users...">
            </div>
            <div class="col-md-4">
                <select class="form-select">
                    <option value="">Filter by Role</option>
                    <option value="Admin">Admin</option>
                    <option value="Teacher">Teacher</option>
                    <option value="Counsellor">Counsellor</option>
                    <option value="Student">Student</option>
                </select>
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-outline-primary w-100">Filter</button>
            </div>
        </form>
    </div>
</div>

<div class="card">
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover mb-0 align-middle">
                <thead class="table-light">
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user.name }}</td>
                        <td>{{ user.email }}</td>
                        <td><span class="badge bg-secondary">{{ user.role }}</span></td>
                        <td>{{ user.created_at }}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary"><i class="fas fa-edit"></i></button>
                            <button class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" class="text-center py-4 text-muted">No users found.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
""")
