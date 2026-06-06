import secrets
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


task_tags = db.Table(
    "task_tags",
    db.Column("task_id", db.Integer, db.ForeignKey("task.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    team = db.relationship("Team", back_populates="memberships")
    user = db.relationship("User", back_populates="team_memberships")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    owned_teams = db.relationship("Team", back_populates="owner", lazy=True)
    team_memberships = db.relationship(
        "TeamMember", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_tasks = db.relationship(
        "Task", foreign_keys="Task.assignee_id", back_populates="assignee", lazy=True
    )
    created_tasks = db.relationship(
        "Task", foreign_keys="Task.creator_id", back_populates="creator", lazy=True
    )
    comments = db.relationship("Comment", back_populates="author", lazy=True)
    attachments = db.relationship("Attachment", back_populates="uploader", lazy=True)
    activities = db.relationship("TaskActivity", back_populates="actor", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def teams(self):
        return [membership.team for membership in self.team_memberships]


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    invite_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    owner = db.relationship("User", back_populates="owned_teams")
    memberships = db.relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
    )
    projects = db.relationship("Project", back_populates="team", cascade="all, delete-orphan")

    @staticmethod
    def generate_invite_code():
        while True:
            code = secrets.token_hex(4).upper()
            if not Team.query.filter_by(invite_code=code).first():
                return code


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    team = db.relationship("Team", back_populates="projects")
    tasks = db.relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="todo")
    priority = db.Column(db.String(20), nullable=False, default="medium")
    assignee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    project = db.relationship("Project", back_populates="tasks")
    assignee = db.relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    creator = db.relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    comments = db.relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    attachments = db.relationship(
        "Attachment", back_populates="task", cascade="all, delete-orphan"
    )
    activities = db.relationship(
        "TaskActivity", back_populates="task", cascade="all, delete-orphan"
    )
    tags = db.relationship("Tag", secondary=task_tags, lazy="subquery", backref="tasks")


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    task = db.relationship("Task", back_populates="comments")
    author = db.relationship("User", back_populates="comments")


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(120), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    task = db.relationship("Task", back_populates="attachments")
    uploader = db.relationship("User", back_populates="attachments")


class TaskActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(120), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    task = db.relationship("Task", back_populates="activities")
    actor = db.relationship("User", back_populates="activities")


class SiteSetting(db.Model):
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    if user is not None and not user.is_active:
        return None
    return user
