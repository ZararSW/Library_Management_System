import os
import logging
from datetime import timedelta

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Setup base for SQLAlchemy
class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
csrf = CSRFProtect()
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///library.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure uploads
app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")
app.config["ORIGINALS_FOLDER"] = os.path.join(app.config["UPLOAD_FOLDER"], "originals")
app.config["THUMBNAILS_FOLDER"] = os.path.join(app.config["UPLOAD_FOLDER"], "thumbnails")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload size

# Configure session
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)  # For "remember me" functionality

# Initialize Flask extensions
db.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

# Ensure upload folders exist
os.makedirs(app.config["ORIGINALS_FOLDER"], exist_ok=True)
os.makedirs(app.config["THUMBNAILS_FOLDER"], exist_ok=True)

# Import models (needed for db.create_all)
from models import User, Book, Member, IssuedBook, BookReview, BookReservation, BookTag, book_tag_association

# Import routes
from routes.auth import auth_bp
from routes.books import books_bp
from routes.members import members_bp
from routes.circulation import circulation_bp
from routes.dashboard import dashboard_bp
from routes.reviews import reviews_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(circulation_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(reviews_bp)

# Setup login manager
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create database and default admin if needed
with app.app_context():
    db.create_all()
    
    # Create default admin user if no users exist
    from werkzeug.security import generate_password_hash
    if not User.query.first():
        from datetime import datetime
        admin = User(
            username="admin",
            email="admin@library.com",
            password_hash=generate_password_hash("admin"),
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Created default admin user.")

# Import and register routes for the root path
from routes import index_page

@app.route('/')
def index():
    return index_page()
