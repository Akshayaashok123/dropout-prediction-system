# EduGuard — AI-Based Early Warning & Student Counselling System

[![Smart India Hackathon Prototype](https://img.shields.io/badge/SIH-Prototype-0d9488.svg)](https://github.com/Akshayaashok123/dropout-prediction-system)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-Academic%20Evaluation-green.svg)](#)

> **Human-in-the-Loop Ethical Guarantee:**
> EduGuard is an institutional early-warning and supportive pastoral counseling tool. Risk indicators are strictly designed to trigger timely faculty mentorship, academic tutoring, and financial guidance. **Predictions never penalize students, automate disciplinary actions, or determine educational eligibility.** All student records in this prototype are synthetic simulation demo data.

---

## 1. System Overview & The Core Workflow

EduGuard transforms raw educational telemetry (lecture attendance, continuous internal assessments, semester exams, and assignment engagements) into transparent, actionable interventions:

```
[Student Telemetry] ──> [Explainable ML Scoring] ──> [Pedagogical Alert]
        │                           │                         │
        ▼                           ▼                         ▼
[Attendance / Marks]        [Random Forest + Rules]      [Mentor Action Queue]
                                                              │
                                                              ▼
[Outcome Tracking]  <─── [Intervention Record] <─── [1-on-1 Mentorship]
```

### The 6-Step Closed-Loop Lifecycle
1. **Student Telemetry Ingestion**: Continuous monitoring of attendance logs, internal quiz scores, backlogs, and assignment timeliness.
2. **Explainable Risk Assessment**: Dual-engine prediction combining a trained **Random Forest Classifier** (`ml/model.joblib`) with a transparent rule-based policy engine.
3. **Transparent Warnings**: Every flagged alert discloses the exact input values, policy reasons, and why faculty review is indicated.
4. **Mentor Action Queue**: Dedicated triage page for faculty and counselors to review high and medium priority cases.
5. **Intervention Tracking**: Authorized staff log structured interactions (support type, contact date, discussion notes, next follow-up date).
6. **Outcome Tracking**: Interventions are monitored through resolution (e.g. remedial tutoring joined, transit barrier resolved) without automatically assuming retention.

---

## 2. Technology Stack & Architecture

- **Backend Framework**: Python 3, Flask 3.0, Flask-Login 0.6, Flask-SQLAlchemy 3.1, Flask-WTF / Werkzeug
- **Database**: SQLite (`instance/dropout.db`) managed via SQLAlchemy ORM
- **Machine Learning**: Scikit-Learn 1.3+ Random Forest Classifier (`ml/model.joblib`), Joblib feature pipeline, Pandas 2.1+
- **Frontend**: Jinja2 templating, Bootstrap 5.3, FontAwesome 6.4, Chart.js 4.4
- **Typography & Theme**: Restrained institutional Navy (`#0f172a`), Teal (`#0d9488`), and clean Off-white surfaces with high-readability mode

---

## 3. Demo Credentials & Synthetic Dataset (Ready to Test)

The database is pre-seeded with **106 user accounts** across 4 distinct role personas, featuring **100 synthetic student records**:

| Role | Email | Password | Primary Console & Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@school.edu` | `admin123` | Institutional command center, batch AI scoring, CSV staging & preview, CSV export, demo reset |
| **Teacher** | `teacher1@school.edu` | `teacher123` | Department roster, classroom alerts, student observations & referrals, attendance trend charts |
| **Counsellor** | `counsellor1@school.edu` | `counsellor123` | Mentor Action Queue, Intervention Tracking Center, 1-on-1 session management |
| **Student** | `student1@school.edu` | `student123` | Non-stigmatizing Academic Wellness Index, study tips, recommendation acknowledgement, AI companion |

*(You can also use the **1-Click Testing Persona** shortcuts on the `/login` screen to sign in instantly without typing).*

---

## 4. Synthetic Dataset Architecture & Telemetry Generation

In educational data science, student records are protected by strict privacy regulations (FERPA, DPDP Act 2023). Because institutional student dropout data cannot be publicly redistributed, this prototype utilizes a **statistically structured synthetic dataset of 100 fictional student profiles**:

### A. Data Schema & Curriculum Alignment
- **Student Profiles (100 records)**: Realistically distributed across 5 academic departments (`Computer Science`, `Electronics & Comm.`, `Mechanical`, `Civil`, `Electrical`) and semesters 1 through 8.
- **Subject Marks (1,500+ records)**: Each department evaluates 5 core discipline subjects with 3 distinct continuous assessment types:
  - `semester` exams (0-100 scale, with scores < 40 recorded as active course backlogs)
  - `internal` mid-term assessments (0-100 scale)
  - `assignment` continuous submissions (0-100 scale)
- **Multi-Week Attendance Telemetry (3,000+ records)**: 35 to 45 daily session logs per student across 50 academic days with explicit `present`, `absent`, and `late` records.

### B. Distinct Evaluative Cohorts & Trend Testing
To demonstrate different triage priorities without hardcoding, the dataset models 5 distinct behavioural archetypes:
1. **Critical Review Cohort (~15 students)**: Low attendance (38-62%), low GPA (2.2-4.2), and 2-4 course backlogs.
2. **Declining Attendance Trajectory (~13 students)**: Started semester with high attendance (85-92%) during early weeks, but experienced a sharp drop to 30-45% in recent weeks (`attendance_trend < -0.15`), demonstrating temporal early-warning detection.
3. **Recovering Attendance Cohort (~8 students)**: Started with poor attendance (40-50%), but rebounded to 80-90% in recent sessions (`attendance_trend > +0.10`) following pastoral check-ins.
4. **Moderate / Borderline Review Cohort (~24 students)**: Attendance hovering between 65-74.5% (approaching statutory 75% limit) and GPA 4.8-6.4.
5. **Stable / Satisfactory Cohort (~40 students)**: Consistent attendance (82-98%), strong GPA (7.2-9.6), and zero backlogs.

---

## 5. Early-Warning Engine: Rules vs. Machine Learning

### A. Configurable Institutional Policy Rules Engine
The core explainability layer relies on deterministic institutional rules (`ml/predictor.py`), configured with explicit policy thresholds:
- **Critical Attendance Deficit**: Attendance < 60.0% (`+35 points`)
- **Low Attendance Warning**: Attendance < 75.0% (`+20 points`)
- **Academic Standing Concern**: GPA < 4.0 (`+30 points`)
- **Moderate Academic Underperformance**: GPA < 5.5 (`+15 points`)
- **Multiple Course Backlogs**: Uncleared semester courses > 2 (`+20 points`)
- **Single Course Backlog**: Uncleared semester course > 0 (`+10 points`)
- **Declining Attendance Trajectory**: Drop between 2nd half and 1st half of attendance records > 15% (`+15 points`)
- **Low Coursework Engagement**: Assignment submission score average < 50% (`+10 points`)

Every flag displays the **actual recorded value** and the **exact policy rule** (e.g., *"Recorded attendance is 54.2%, critically below institutional minimum (60.0%)"*), ensuring mentors understand the precise pedagogical reason.

### B. Preserved Machine Learning Model
- **Algorithm**: `RandomForestClassifier` (`ml/model.joblib`), trained on synthetic dataset `ml/student_dataset.csv`.
- **Target Column**: `dropped_out` (binary: 0 or 1).
- **Features Pipeline (9 numeric markers)**:
  `['attendance_pct', 'gpa', 'internal_marks_avg', 'semester_marks_avg', 'assignment_score_avg', 'backlogs_count', 'attendance_trend', 'marks_trend', 'engagement_score']`
- **Advisory Role**: The model computes a probability score labeled transparently as `"Preserved Random Forest Classifier (Synthetic Training Demonstration)"`. **We do not claim real-world model accuracy or production validation.**

### C. Requirements for Real-World Validation
Before deploying an ML dropout prediction system in a live university:
1. **Ethical IRB & Privacy Clearance**: Institutional Review Board clearance and data anonymization following the Digital Personal Data Protection (DPDP) Act.
2. **Multi-Year Longitudinal Ground Truth**: Retrospective historical datasets across multiple graduating cohorts (4+ years) linking admissions, socio-economic factors, transit constraints, and verified degree completion.
3. **Fairness & Bias Auditing**: Rigorous demographic parity and disparate impact testing to ensure algorithms do not disproportionately flag underrepresented groups.
4. **Calibration on Real Intervention Feedback**: Continual recalibration incorporating student feedback and post-mentorship outcome trajectories.

---

## 6. Setup, Startup Loading & Sample CSV

### Application Startup & Automatic Data Loading
On startup, `app.py` automatically initializes database tables and verifies baseline data presence via `seed_data.ensure_seed_data()`. If the database is fresh, it loads the 100-student synthetic dataset automatically. If records already exist, it skips seeding to prevent duplicate entries.

```bash
# 1. Install required dependencies
pip install -r requirements.txt
pip install flask-login flask-sqlalchemy flask-wtf pytest

# 2. Start the application (auto-seeds on first launch)
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

### Downloadable Sample Import CSV
Administrators can download the exact import format template from:
- Directory Toolbar button: **"Sample CSV"**
- Modal link inside: **"Upload Student Dataset (CSV)"**
- Direct API endpoint: **`/admin/students/sample-csv`**

### Supported CSV Schema
```csv
name,email,department,semester,attendance,gpa,phone
"Aarav Mehta",demo.student1@school.edu,Computer Science,3,58.5,3.60,555-0101
"Diya Patel",demo.student2@school.edu,Electronics & Comm.,4,64.0,5.10,555-0102
"Vikram Singh",demo.student3@school.edu,Mechanical,2,88.5,8.20,555-0103
```

### Validation & Merge Rules
1. **Header Validation**: Checks presence of `name`, `email`, and `department`.
2. **Range & Type Checking**: 
   - `attendance`: Valid float between `0.0` and `100.0%`
   - `gpa`: Valid float between `0.0` and `10.0` scale
   - `semester`: Integer between `1` and `12`
3. **No Silent Discards**: Rows containing errors (e.g. GPA `14.5` or malformed email) are explicitly isolated in a **Rejected Rows** table with detailed reasons.
4. **Deterministic Merge**:
   - If `email` exists in the system: Updates semester, department, attendance, and GPA.
   - If `email` is new: Creates a new Student profile.
5. **Instant Rescoring**: On confirmation, newly imported records are scored by the early-warning pipeline and immediately reflected in dashboard charts.

---

## 6. Model vs. Rules Disclosure

In accordance with responsible AI standards:
- **Supervised ML Probability**: The Random Forest model (`ml/model.joblib`) computes early-warning propensity based on 9 engineered features:
  - `attendance_pct` (Presence rate from actual lecture sessions)
  - `gpa` (Continuous performance scale)
  - `internal_marks_avg` & `semester_marks_avg`
  - `assignment_score_avg`
  - `backlogs_count` (Count of semester exams with score < 40)
  - `attendance_trend` (Trajectory comparing early vs recent sessions)
  - `marks_trend`
  - `engagement_score` (Weighted attendance and submission index)
- **Pedagogical Rule Explanations**: Contributing factors displayed to mentors (e.g., *"Critical Attendance Deficit: 58.2% (below 75% norm)"*) are explicitly labeled by their source policy so educators understand the transparent rationale.

---

## 7. Running the Test Suite

The test suite validates prediction output structures, role-based route access, CSV import staging, and the intervention CRUD lifecycle:

```bash
# Run pytest in verbose mode
python -m pytest tests/test_application.py -v
```

---

## 8. Limitations & Planned Extensions

- **SMS / WhatsApp Integration**: In this prototype, notifications are stored internally within the application. Outbound SMS/WhatsApp gateways would be configured via institutional Twilio/SMS APIs in production.
- **Socioeconomic Neutrality**: Sensitive demographic information is not used as direct predictive features to avoid reinforcing historical systemic disparities.
- **Biometric Integration**: Attendance records in this prototype are generated from daily subject lecture logs; production deployment would link directly to institutional RFID/biometric turnstiles.

