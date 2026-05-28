from pathlib import Path

from flask import Flask

from config import Config
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.projects import bp as projects_bp
    from app.tasks import bp as tasks_bp
    from app.analytics import bp as analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(analytics_bp)

    with app.app_context():
        from app import models  # noqa: F401

    return app
