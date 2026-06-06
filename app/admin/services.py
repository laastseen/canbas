import os
from datetime import date, datetime, timedelta

from sqlalchemy import func

from app.extensions import db
from app.models import (
    Attachment,
    Comment,
    Project,
    SiteSetting,
    Task,
    TaskActivity,
    Team,
    TeamMember,
    User,
)

DEFAULT_SETTINGS = {
    "site_name": "Canbas",
    "max_upload_mb": "16",
    "blocked_email_domains": "",
    "registration_enabled": "true",
}


def get_setting(key: str, default: str | None = None) -> str:
    row = db.session.get(SiteSetting, key)
    if row is None:
        return default if default is not None else DEFAULT_SETTINGS.get(key, "")
    return row.value


def set_setting(key: str, value: str):
    row = db.session.get(SiteSetting, key)
    if row is None:
        row = SiteSetting(key=key, value=value)
        db.session.add(row)
    else:
        row.value = value


def ensure_default_settings():
    for key, value in DEFAULT_SETTINGS.items():
        if db.session.get(SiteSetting, key) is None:
            db.session.add(SiteSetting(key=key, value=value))
    db.session.commit()


def dashboard_stats():
    today = date.today()
    week_ago = today - timedelta(days=6)
    registrations = (
        db.session.query(func.date(User.created_at), func.count(User.id))
        .filter(User.created_at >= datetime.combine(week_ago, datetime.min.time()))
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )
    reg_map = {str(day): count for day, count in registrations}
    reg_chart = [
        {"day": (week_ago + timedelta(days=i)).strftime("%d.%m"), "count": reg_map.get(str(week_ago + timedelta(days=i)), 0)}
        for i in range(7)
    ]

    tasks_by_status = dict(
        db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    )

    upload_bytes = db.session.query(func.sum(func.length(Attachment.file_path))).scalar() or 0
    upload_dir = db.session.query(Attachment.file_path).first()
    disk_usage = 0
    if upload_dir:
        folder = os.path.dirname(upload_dir[0])
        if os.path.isdir(folder):
            for root, _, files in os.walk(folder):
                for name in files:
                    try:
                        disk_usage += os.path.getsize(os.path.join(root, name))
                    except OSError:
                        pass

    return {
        "users": User.query.count(),
        "teams": Team.query.count(),
        "projects": Project.query.count(),
        "tasks": Task.query.count(),
        "comments": Comment.query.count(),
        "attachments": Attachment.query.count(),
        "tasks_todo": tasks_by_status.get("todo", 0),
        "tasks_in_progress": tasks_by_status.get("in_progress", 0),
        "tasks_done": tasks_by_status.get("done", 0),
        "overdue": Task.query.filter(Task.due_date < today, Task.status != "done").count(),
        "reg_chart": reg_chart,
        "top_teams": _top_teams(),
        "recent_activity": (
            TaskActivity.query.order_by(TaskActivity.created_at.desc()).limit(15).all()
        ),
        "disk_usage_mb": round(disk_usage / (1024 * 1024), 1),
    }


def _top_teams(limit=5):
    rows = (
        db.session.query(Team.name, func.count(Task.id))
        .join(Project, Project.team_id == Team.id)
        .join(Task, Task.project_id == Project.id)
        .group_by(Team.id)
        .order_by(func.count(Task.id).desc())
        .limit(limit)
        .all()
    )
    return [{"name": name, "tasks": count} for name, count in rows]


def delete_attachment_file(attachment: Attachment):
    if attachment.file_path and os.path.isfile(attachment.file_path):
        os.remove(attachment.file_path)
