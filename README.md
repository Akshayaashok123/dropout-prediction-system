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

## 3. Demo Credentials (Ready to Test)

The database is pre-seeded with 56 user accounts across 4 distinct role personas:

| Role | Email | Password | Primary Console & Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@school.edu` | `admin123` | Institutional command center, batch AI scoring, CSV staging & preview, demo reset |
| **Teacher** | `teacher1@school.edu` | `teacher123` | Department roster, classroom alerts, student observations & referrals |
| **Counsellor** | `counsellor1@school.edu` | `counsellor123` | Mentor Action Queue, Intervention Tracking Center, 1-on-1 session management |
| **Student** | `student1@school.edu` | `student123` | Non-stigmatizing Academic Wellness Index, study tips, recommendation acknowledgement, AI companion |

*(You can also use the **1-Click Testing Persona** buttons on the `/login` screen to sign in instantly without typing).*

---

## 4. Setup & Running the Application

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed
- Git

### Installation
```bash
# 1. Clone repository (if not already local)
git clone https://github.com/Akshayaashok123/dropout-prediction-system.git
cd dropout-prediction-system

# 2. Install required dependencies
pip install -r requirements.txt
pip install flask-login flask-sqlalchemy flask-wtf pytest

# 3. Seed demo database with synthetic students, attendance, marks & interventions
python seed_data.py

# 4. Start the Flask application
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 5. CSV Import & Data Validation Workflow

EduGuard provides a robust **Stage & Preview** data ingestion pipeline (`/admin/students` -> Upload CSV):

### Supported CSV Format
```csv
name,email,department,semester,attendance,gpa,phone
Aarav Mehta,aarav.mehta@school.edu,Computer Science,4,62.5,4.8,555-0192
Diya Sen,diya.sen@school.edu,Electronics & Comm.,2,88.0,8.2,555-0145
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

