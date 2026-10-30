import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # ── Register Blueprints ──────────────────────────────────────────
    from routes.auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from routes.admin import admin as admin_bp
    app.register_blueprint(admin_bp)

    from routes.teacher import teacher as teacher_bp
    app.register_blueprint(teacher_bp)

    from routes.counsellor import counsellor as counsellor_bp
    app.register_blueprint(counsellor_bp)

    from routes.student import student as student_bp
    app.register_blueprint(student_bp)

    # ── Error Handlers ───────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # ── Context Processors ───────────────────────────────────────────
    @app.context_processor
    def utility_processor():
        def format_date(d):
            if d:
                return d.strftime('%Y-%m-%d')
            return ""
        def format_datetime(d):
            if d:
                return d.strftime('%Y-%m-%d %H:%M')
            return ""
        return dict(format_date=format_date, format_datetime=format_datetime)
        
    # ── Landing Page ─────────────────────────────────────────────────
    @app.route('/')
    def index():
        return render_template('landing.html')

    # ── Create Tables & Ensure Baseline Demonstration Data ─────────────
    with app.app_context():
        db.create_all()
        try:
            from seed_data import ensure_seed_data
            ensure_seed_data()
        except Exception as e:
            app.logger.warning(f"Startup demonstration data seeding notice: {e}")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
