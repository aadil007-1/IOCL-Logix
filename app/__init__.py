import os
from flask import Flask
from config import Config
from app.extensions import init_supabase

def create_app(config_class=Config):
    # Set the static folder to public
    app = Flask(__name__, static_folder='../public')
    app.config.from_object(config_class)

    # Initialize extensions
    init_supabase(app)

    # Register blueprints
    from app.routes.auth_routes import bp as auth_bp
    from app.routes.dashboard_routes import bp as dashboard_bp
    from app.routes.admin_routes import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)

    return app
