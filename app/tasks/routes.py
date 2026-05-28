import os
from datetime import date

from flask import flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Attachment, Comment, Task, TeamMember
from app.tasks import bp
from app.tasks.forms import AttachmentForm, CommentForm, TaskForm
from app.tasks.services import (
    get_project_or_404,
    get_task_or_404,
    parse_tags,
    record_activity,
    save_attachment,
)


@bp.route("/project/<int:project_id>")
@login_required
def project_tasks(project_id):
    project = get_project_or_404(project_id)
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    priority_filter = request.args.get("priority", "")
    assignee_filter = request.args.get("assignee", 0, type=int)

    query = Task.query.filter_by(project_id=project.id)
    if q:
        query = query.filter(
            Task.title.ilike(f"%{q}%") | Task.description.ilike(f"%{q}%")
        )
    if status_filter in {"todo", "in_progress", "done"}:
        query = query.filter_by(status=status_filter)
    if priority_filter in {"low", "medium", "high"}:
        query = query.filter_by(priority=priority_filter)
    if assignee_filter:
        query = query.filter_by(assignee_id=assignee_filter)

    pagination = query.order_by(Task.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    members = TeamMember.query.filter_by(team_id=project.team_id).all()
    return render_template(
        "tasks/list.html",
        project=project,
        tasks=pagination.items,
        pagination=pagination,
        members=members,
        q=q,
        status_filter=status_filter,
        priority_filter=priority_filter,
        assignee_filter=assignee_filter,
        today=date.today(),
    )


@bp.route("/project/<int:project_id>/create", methods=["GET", "POST"])
@login_required
def create_task(project_id):
    project = get_project_or_404(project_id)
    form = TaskForm()
    members = TeamMember.query.filter_by(team_id=project.team_id).all()
    form.assignee_id.choices = [(0, "Без исполнителя")] + [
        (member.user.id, member.user.username) for member in members
    ]

    if form.validate_on_submit():
        task = Task(
            project_id=project.id,
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            assignee_id=form.assignee_id.data or None,
            creator_id=current_user.id,
            due_date=form.due_date.data,
        )
        task.tags = parse_tags(form.tags.data)
        db.session.add(task)
        record_activity(task, current_user.id, "task_created", task.title)
        db.session.commit()

        flash("Задача успешно создана.", "success")
        return redirect(url_for("tasks.project_tasks", project_id=project.id))

    return render_template("tasks/form.html", form=form, project=project, title="Создать задачу")


@bp.route("/<int:task_id>", methods=["GET", "POST"])
@login_required
def task_detail(task_id):
    task = get_task_or_404(task_id)
    comment_form = CommentForm(prefix="comment")
    attachment_form = AttachmentForm(prefix="attachment")

    if comment_form.submit.data and comment_form.validate_on_submit():
        comment = Comment(task_id=task.id, author_id=current_user.id, body=comment_form.body.data)
        db.session.add(comment)
        record_activity(task, current_user.id, "comment_added")
        db.session.commit()
        flash("Комментарий добавлен.", "success")
        return redirect(url_for("tasks.task_detail", task_id=task.id))

    if attachment_form.submit.data and attachment_form.validate_on_submit():
        save_attachment(task, attachment_form.file.data)
        db.session.commit()
        flash("Файл успешно загружен.", "success")
        return redirect(url_for("tasks.task_detail", task_id=task.id))

    return render_template(
        "tasks/detail.html",
        task=task,
        comment_form=comment_form,
        attachment_form=attachment_form,
    )


@bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = get_task_or_404(task_id)
    form = TaskForm(obj=task)
    members = TeamMember.query.filter_by(team_id=task.project.team_id).all()
    form.assignee_id.choices = [(0, "Без исполнителя")] + [
        (member.user.id, member.user.username) for member in members
    ]

    if request.method == "GET":
        form.assignee_id.data = task.assignee_id or 0
        form.tags.data = ", ".join(tag.name for tag in task.tags)

    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.status = form.status.data
        task.priority = form.priority.data
        task.assignee_id = form.assignee_id.data or None
        task.due_date = form.due_date.data
        task.tags = parse_tags(form.tags.data)
        record_activity(task, current_user.id, "task_updated", task.title)
        db.session.commit()

        flash("Задача успешно обновлена.", "success")
        return redirect(url_for("tasks.task_detail", task_id=task.id))

    return render_template("tasks/form.html", form=form, project=task.project, title="Редактировать задачу")


@bp.route("/<int:task_id>/board-update", methods=["POST"])
@login_required
def board_update(task_id):
    task = get_task_or_404(task_id)
    status = request.form.get("status") or (request.json or {}).get("status")
    if status not in {"todo", "in_progress", "done"}:
        return jsonify({"success": False}), 400

    task.status = status
    record_activity(task, current_user.id, "status_changed", status)
    db.session.commit()
    return jsonify({"success": True, "status": status})


@bp.route("/project/<int:project_id>/board")
@login_required
def board(project_id):
    project = get_project_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project.id).all()
    columns = {
        "todo": [task for task in tasks if task.status == "todo"],
        "in_progress": [task for task in tasks if task.status == "in_progress"],
        "done": [task for task in tasks if task.status == "done"],
    }
    return render_template("tasks/board.html", project=project, columns=columns)


@bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = get_task_or_404(task_id)
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash("Задача удалена.", "success")
    return redirect(url_for("tasks.project_tasks", project_id=project_id))


@bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        return redirect(url_for("main.dashboard"))
    task = get_task_or_404(comment.task_id)
    if comment.author_id != current_user.id:
        flash("Нельзя удалить чужой комментарий.", "danger")
        return redirect(url_for("tasks.task_detail", task_id=task.id))
    db.session.delete(comment)
    db.session.commit()
    flash("Комментарий удалён.", "success")
    return redirect(url_for("tasks.task_detail", task_id=task.id))


@bp.route("/attachments/<int:attachment_id>/delete", methods=["POST"])
@login_required
def delete_attachment(attachment_id):
    attachment = db.session.get(Attachment, attachment_id)
    if attachment is None:
        return redirect(url_for("main.dashboard"))
    task = get_task_or_404(attachment.task_id)
    if attachment.uploader_id != current_user.id:
        flash("Нельзя удалить чужое вложение.", "danger")
        return redirect(url_for("tasks.task_detail", task_id=task.id))
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
    db.session.delete(attachment)
    db.session.commit()
    flash("Вложение удалено.", "success")
    return redirect(url_for("tasks.task_detail", task_id=task.id))


@bp.route("/attachments/<int:attachment_id>/download")
@login_required
def download_attachment(attachment_id):
    attachment = next(
        (
            item
            for membership in current_user.team_memberships
            for project in membership.team.projects
            for task in project.tasks
            for item in task.attachments
            if item.id == attachment_id
        ),
        None,
    )
    if attachment is None or not os.path.exists(attachment.file_path):
        return redirect(url_for("main.dashboard"))

    return send_file(attachment.file_path, as_attachment=True, download_name=attachment.original_name)
