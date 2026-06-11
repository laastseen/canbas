from datetime import date

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.admin import bp
from app.admin.decorators import superadmin_required
from app.admin.services import (
    dashboard_stats,
    delete_attachment_file,
    ensure_default_settings,
    get_setting,
    set_setting,
)
from app.extensions import db
from app.models import (
    Attachment,
    Comment,
    ConsentLog,
    Project,
    Tag,
    Task,
    TaskActivity,
    Team,
    TeamMember,
    User,
)


@bp.route("/")
@login_required
@superadmin_required
def dashboard():
    return render_template("admin/dashboard.html", stats=dashboard_stats())


@bp.route("/users")
@login_required
@superadmin_required
def users():
    q = request.args.get("q", "").strip()
    query = User.query.order_by(User.created_at.desc())
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.username.ilike(like), User.email.ilike(like)))
    return render_template("admin/users.html", users=query.all(), q=q)


@bp.route("/users/<int:user_id>", methods=["GET", "POST"])
@login_required
@superadmin_required
def user_detail(user_id):
    user = db.session.get(User, user_id) or abort404()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "toggle_active":
            if user.id == current_user.id:
                flash("Нельзя заблокировать самого себя.", "danger")
            else:
                user.is_active = not user.is_active
                db.session.commit()
                flash("Статус пользователя обновлён.", "success")
        elif action == "toggle_superadmin":
            if user.id == current_user.id:
                flash("Нельзя снять права у самого себя.", "danger")
            else:
                user.is_superadmin = not user.is_superadmin
                db.session.commit()
                flash("Права администратора обновлены.", "success")
        elif action == "reset_password":
            new_password = request.form.get("new_password", "").strip()
            if len(new_password) < 6:
                flash("Пароль должен быть не короче 6 символов.", "danger")
            else:
                user.set_password(new_password)
                db.session.commit()
                flash("Пароль сброшен.", "success")
        elif action == "update_profile":
            user.username = request.form.get("username", user.username).strip()
            user.email = request.form.get("email", user.email).strip().lower()
            db.session.commit()
            flash("Профиль обновлён.", "success")
        return redirect(url_for("admin.user_detail", user_id=user.id))

    memberships = TeamMember.query.filter_by(user_id=user.id).all()
    return render_template("admin/user_detail.html", user=user, memberships=memberships)


@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@superadmin_required
def user_delete(user_id):
    user = db.session.get(User, user_id) or abort404()
    if user.id == current_user.id:
        flash("Нельзя удалить самого себя.", "danger")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash("Пользователь удалён.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/teams")
@login_required
@superadmin_required
def teams():
    all_teams = Team.query.order_by(Team.created_at.desc()).all()
    return render_template("admin/teams.html", teams=all_teams)


@bp.route("/teams/<int:team_id>", methods=["GET", "POST"])
@login_required
@superadmin_required
def team_detail(team_id):
    team = db.session.get(Team, team_id) or abort404()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update":
            team.name = request.form.get("name", team.name).strip()
            owner_id = request.form.get("owner_id", type=int)
            if owner_id:
                team.owner_id = owner_id
            db.session.commit()
            flash("Команда обновлена.", "success")
        elif action == "regenerate_code":
            team.invite_code = Team.generate_invite_code()
            db.session.commit()
            flash(f"Новый код: {team.invite_code}", "info")
        elif action == "delete":
            db.session.delete(team)
            db.session.commit()
            flash("Команда удалена.", "success")
            return redirect(url_for("admin.teams"))
        return redirect(url_for("admin.team_detail", team_id=team.id))

    members = TeamMember.query.filter_by(team_id=team.id).all()
    projects = Project.query.filter_by(team_id=team.id).all()
    return render_template(
        "admin/team_detail.html", team=team, members=members, projects=projects
    )


@bp.route("/projects")
@login_required
@superadmin_required
def projects():
    all_projects = (
        Project.query.join(Team).order_by(Project.created_at.desc()).all()
    )
    return render_template("admin/projects.html", projects=all_projects)


@bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
@superadmin_required
def project_delete(project_id):
    project = db.session.get(Project, project_id) or abort404()
    db.session.delete(project)
    db.session.commit()
    flash("Проект удалён.", "success")
    return redirect(url_for("admin.projects"))


@bp.route("/tasks")
@login_required
@superadmin_required
def tasks():
    status = request.args.get("status", "")
    query = Task.query.join(Project).order_by(Task.updated_at.desc())
    if status:
        query = query.filter(Task.status == status)
    return render_template("admin/tasks.html", tasks=query.limit(200).all(), status=status)


@bp.route("/tasks/bulk", methods=["POST"])
@login_required
@superadmin_required
def tasks_bulk():
    ids = request.form.getlist("task_ids")
    action = request.form.get("bulk_action")
    if not ids:
        flash("Задачи не выбраны.", "warning")
        return redirect(url_for("admin.tasks"))
    tasks = Task.query.filter(Task.id.in_(ids)).all()
    if action == "delete":
        for task in tasks:
            db.session.delete(task)
        flash(f"Удалено задач: {len(tasks)}.", "success")
    elif action in ("todo", "in_progress", "done"):
        for task in tasks:
            task.status = action
        flash(f"Статус обновлён у {len(tasks)} задач.", "success")
    db.session.commit()
    return redirect(url_for("admin.tasks", status=request.form.get("status_filter", "")))


@bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
@superadmin_required
def task_delete(task_id):
    task = db.session.get(Task, task_id) or abort404()
    db.session.delete(task)
    db.session.commit()
    flash("Задача удалена.", "success")
    return redirect(url_for("admin.tasks"))


@bp.route("/attachments")
@login_required
@superadmin_required
def attachments():
    files = Attachment.query.order_by(Attachment.uploaded_at.desc()).limit(200).all()
    return render_template("admin/attachments.html", attachments=files)


@bp.route("/attachments/<int:attachment_id>/delete", methods=["POST"])
@login_required
@superadmin_required
def attachment_delete(attachment_id):
    attachment = db.session.get(Attachment, attachment_id) or abort404()
    delete_attachment_file(attachment)
    db.session.delete(attachment)
    db.session.commit()
    flash("Вложение удалено.", "success")
    return redirect(url_for("admin.attachments"))


@bp.route("/tags", methods=["GET", "POST"])
@login_required
@superadmin_required
def tags():
    if request.method == "POST":
        action = request.form.get("action")
        tag_id = request.form.get("tag_id", type=int)
        tag = db.session.get(Tag, tag_id) if tag_id else None
        if action == "rename" and tag:
            tag.name = request.form.get("name", tag.name).strip().lower()
            db.session.commit()
            flash("Тег переименован.", "success")
        elif action == "delete" and tag:
            db.session.delete(tag)
            db.session.commit()
            flash("Тег удалён.", "success")
        return redirect(url_for("admin.tags"))
    return render_template("admin/tags.html", tags=Tag.query.order_by(Tag.name).all())


@bp.route("/activity")
@login_required
@superadmin_required
def activity():
    items = TaskActivity.query.order_by(TaskActivity.created_at.desc()).limit(100).all()
    return render_template("admin/activity.html", activities=items)


@bp.route("/consents")
@login_required
@superadmin_required
def consents():
    logs = ConsentLog.query.order_by(ConsentLog.created_at.desc()).limit(200).all()
    return render_template("admin/consents.html", logs=logs)


@bp.route("/settings", methods=["GET", "POST"])
@login_required
@superadmin_required
def settings():
    ensure_default_settings()
    if request.method == "POST":
        set_setting("site_name", request.form.get("site_name", "Canbas").strip())
        set_setting("max_upload_mb", request.form.get("max_upload_mb", "16").strip())
        set_setting("blocked_email_domains", request.form.get("blocked_email_domains", "").strip())
        set_setting(
            "registration_enabled",
            "true" if request.form.get("registration_enabled") else "false",
        )
        db.session.commit()
        flash("Настройки сохранены.", "success")
        return redirect(url_for("admin.settings"))

    return render_template(
        "admin/settings.html",
        site_name=get_setting("site_name"),
        max_upload_mb=get_setting("max_upload_mb"),
        blocked_email_domains=get_setting("blocked_email_domains"),
        registration_enabled=get_setting("registration_enabled") == "true",
    )


def abort404():
    from flask import abort

    abort(404)
