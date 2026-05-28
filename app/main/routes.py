from flask import render_template
from flask_login import current_user, login_required

from app.main import bp
from app.models import Project, Task, Team


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return render_template("main/index.html", dashboard=True)
    return render_template("main/landing.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    memberships = current_user.team_memberships
    team_ids = [m.team_id for m in memberships]
    teams = Team.query.filter(Team.id.in_(team_ids)).all() if team_ids else []
    projects = Project.query.filter(Project.team_id.in_(team_ids)).all() if team_ids else []
    assigned_tasks = Task.query.filter_by(assignee_id=current_user.id).order_by(Task.due_date.asc()).all()
    admin_team_ids = {m.team_id for m in memberships if m.role == "admin"}
    return render_template(
        "main/index.html",
        teams=teams,
        projects=projects,
        assigned_tasks=assigned_tasks,
        admin_team_ids=admin_team_ids,
        dashboard=False,
    )
