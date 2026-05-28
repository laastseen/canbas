from datetime import date

from sqlalchemy import func
from flask import render_template
from flask_login import current_user, login_required

from app.analytics import bp
from app.models import Project, Task, User


def user_project_ids():
    team_ids = [membership.team_id for membership in current_user.team_memberships]
    if not team_ids:
        return []
    return [project.id for project in Project.query.filter(Project.team_id.in_(team_ids)).all()]


@bp.route("/")
@login_required
def overview():
    project_ids = user_project_ids()
    if not project_ids:
        return render_template("analytics/overview.html", stats={}, workload=[], projects_progress=[], overdue=[])

    tasks_q = Task.query.filter(Task.project_id.in_(project_ids))
    total = tasks_q.count()
    done = tasks_q.filter_by(status="done").count()
    stats = {
        "total": total,
        "todo": tasks_q.filter_by(status="todo").count(),
        "in_progress": tasks_q.filter_by(status="in_progress").count(),
        "done": done,
        "high_priority": tasks_q.filter_by(priority="high").count(),
        "done_pct": round(done / total * 100) if total else 0,
    }

    raw_workload = (
        Task.query.with_entities(Task.assignee_id, func.count(Task.id))
        .filter(Task.project_id.in_(project_ids), Task.assignee_id.isnot(None))
        .group_by(Task.assignee_id)
        .all()
    )
    user_ids = [row[0] for row in raw_workload]
    users = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()}
    workload = [(users.get(uid, f"#{uid}"), count) for uid, count in raw_workload]

    projects = Project.query.filter(Project.id.in_(project_ids)).all()
    projects_progress = []
    for project in projects:
        p_total = Task.query.filter_by(project_id=project.id).count()
        p_done = Task.query.filter_by(project_id=project.id, status="done").count()
        projects_progress.append({
            "name": project.name,
            "total": p_total,
            "done": p_done,
            "pct": round(p_done / p_total * 100) if p_total else 0,
        })

    overdue = (
        Task.query.filter(
            Task.project_id.in_(project_ids),
            Task.due_date < date.today(),
            Task.status != "done",
        )
        .order_by(Task.due_date.asc())
        .all()
    )

    return render_template(
        "analytics/overview.html",
        stats=stats,
        workload=workload,
        projects_progress=projects_progress,
        overdue=overdue,
    )
