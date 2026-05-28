import os
import uuid
from pathlib import Path

from flask import abort, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Attachment, Project, Tag, Task, TaskActivity, TeamMember


def ensure_project_access(project: Project):
    membership = TeamMember.query.filter_by(team_id=project.team_id, user_id=current_user.id).first()
    if membership is None:
        abort(403)
    return membership


def get_project_or_404(project_id: int):
    project = db.session.get(Project, project_id)
    if project is None:
        abort(404)
    ensure_project_access(project)
    return project


def get_task_or_404(task_id: int):
    task = db.session.get(Task, task_id)
    if task is None:
        abort(404)
    ensure_project_access(task.project)
    return task


def parse_tags(raw_tags: str):
    if not raw_tags:
        return []

    names = {tag.strip().lower() for tag in raw_tags.split(",") if tag.strip()}
    tags = []
    for name in names:
        tag = Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name)
            db.session.add(tag)
        tags.append(tag)
    return tags


def record_activity(task: Task, actor_id: int, action: str, details: str | None = None):
    activity = TaskActivity(task=task, actor_id=actor_id, action=action, details=details)
    db.session.add(activity)


def allowed_file(filename: str):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return extension in current_app.config["ALLOWED_EXTENSIONS"]


def save_attachment(task: Task, storage):
    if storage is None or storage.filename == "":
        abort(400)
    if not allowed_file(storage.filename):
        abort(400)

    original_name = secure_filename(storage.filename)
    suffix = Path(original_name).suffix
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, stored_name)
    storage.save(file_path)

    attachment = Attachment(
        task=task,
        uploader_id=current_user.id,
        original_name=original_name,
        stored_name=stored_name,
        file_path=file_path,
        mime_type=storage.mimetype,
    )
    db.session.add(attachment)
    record_activity(task, current_user.id, "attachment_uploaded", original_name)
    return attachment
