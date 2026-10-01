from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)  # קידומת לכתובות השרתים
    email = db.Column(db.String(255), unique=True, nullable=True)
    google_sub = db.Column(db.String(64), unique=True, nullable=True)  # מזהה יציב של חשבון Google
    password_hash = db.Column(db.String(255), nullable=True)  # None = משתמש Google בלבד, אין כניסה בסיסמה
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    routes = db.relationship("Route", backref="owner", lazy=True, cascade="all, delete-orphan")
    api_keys = db.relationship("ApiKey", backref="owner", lazy=True, cascade="all, delete-orphan")


class ApiKey(db.Model):
    """מפתח API אחד לכל ספק (anthropic / openai / gemini) לכל משתמש. נשמר מוצפן."""

    __tablename__ = "api_keys"
    __table_args__ = (db.UniqueConstraint("user_id", "provider", name="uq_user_provider"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    provider = db.Column(db.String(20), nullable=False)
    encrypted_key = db.Column(db.Text, nullable=False)


class Route(db.Model):
    __tablename__ = "routes"
    __table_args__ = (db.UniqueConstraint("user_id", "route_name", name="uq_user_route"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    route_name = db.Column(db.String(40), nullable=False)
    full_path = db.Column(db.String(150), unique=True, nullable=False)
    source_lang = db.Column(db.String(30), nullable=True)

    # pending = ממתין לאישור מנהל | active = פעיל | rejected = נדחה
    status = db.Column(db.String(20), default="pending", nullable=False)
    live_code = db.Column(db.Text, nullable=True)  # הגרסה המאושרת שרצה בפועל
    pending_code = db.Column(db.Text, nullable=True)  # גרסה שממתינה לבדיקה
    live_version = db.Column(db.Integer, default=0, nullable=False)  # עולה בכל אישור, מרענן cache בין workers

    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    logs = db.relationship("Log", backref="route", lazy=True, cascade="all, delete-orphan")


class Log(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=utcnow)
    message = db.Column(db.Text, nullable=False)
