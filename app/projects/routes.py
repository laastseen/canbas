from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Project, Team, TeamMember
from app.projects import bp
from app.projects.forms import JoinTeamForm, ProjectForm, TeamForm


@bp.route("/teams/<int:team_id>/promote/<int:user_id>", methods=["POST"])
@login_required
def promote_member(team_id, user_id):
    team = db.session.get(Team, team_id)
    if team is None or team.owner_id != current_user.id:
        flash("Только владелец может менять роли.", "danger")
        return redirect(url_for("projects.team_detail", team_id=team_id))
    target = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if target and target.role != "admin":
        target.role = "admin"
        db.session.commit()
        flash("Участник повышен до администратора.", "success")
    return redirect(url_for("projects.team_detail", team_id=team_id))


@bp.route("/teams/<int:team_id>/demote/<int:user_id>", methods=["POST"])
@login_required
def demote_member(team_id, user_id):
    team = db.session.get(Team, team_id)
    if team is None or team.owner_id != current_user.id:
        flash("Только владелец может менять роли.", "danger")
        return redirect(url_for("projects.team_detail", team_id=team_id))
    if user_id == team.owner_id:
        flash("Нельзя понизить владельца.", "danger")
        return redirect(url_for("projects.team_detail", team_id=team_id))
    target = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if target and target.role != "member":
        target.role = "member"
        db.session.commit()
        flash("Участник понижен до обычного участника.", "success")
    return redirect(url_for("projects.team_detail", team_id=team_id))


@bp.route("/teams/<int:team_id>/leave", methods=["POST"])
@login_required
def leave_team(team_id):
    team = db.session.get(Team, team_id)
    if team is None:
        return redirect(url_for("main.dashboard"))
    if team.owner_id == current_user.id:
        flash("Владелец не может покинуть команду.", "danger")
        return redirect(url_for("projects.team_detail", team_id=team_id))
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash(f"Вы покинули команду «{team.name}».", "success")
    return redirect(url_for("main.dashboard"))


@bp.route("/teams/<int:team_id>/regenerate-code", methods=["POST"])
@login_required
def regenerate_invite_code(team_id):
    team = db.session.get(Team, team_id)
    if team is None:
        return redirect(url_for("main.dashboard"))
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id, role="admin").first()
    if membership is None:
        flash("Только администратор может обновить код приглашения.", "danger")
        return redirect(url_for("projects.team_detail", team_id=team_id))
    team.invite_code = Team.generate_invite_code()
    db.session.commit()
    flash("Код приглашения обновлён.", "success")
    return redirect(url_for("projects.team_detail", team_id=team_id))


@bp.route("/teams/<int:team_id>")
@login_required
def team_detail(team_id):
    team = db.session.get(Team, team_id)
    if team is None:
        return redirect(url_for("main.dashboard"))
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if membership is None:
        return redirect(url_for("main.dashboard"))
    return render_template("projects/team_detail.html", team=team, my_role=membership.role)


@bp.route("/teams/<int:team_id>/remove/<int:user_id>", methods=["POST"])
@login_required
def remove_member(team_id, user_id):
    team = db.session.get(Team, team_id)
    if team is None:
        return redirect(url_for("main.dashboard"))
    admin_membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id, role="admin").first()
    if admin_membership is None:
        flash("Только администратор может исключать участников.", "danger")
        return redirect(url_for("projects.team_detail", team_id=team_id))
    if user_id == team.owner_id:
        flash("Нельзя исключить владельца команды.", "danger")
        return redirect(url_for("projects.team_detail", team_id=team_id))
    target = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if target:
        db.session.delete(target)
        db.session.commit()
        flash("Участник исключён из команды.", "success")
    return redirect(url_for("projects.team_detail", team_id=team_id))


@bp.route("/teams/create", methods=["GET", "POST"])
@login_required
def create_team():
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(
            name=form.name.data,
            owner_id=current_user.id,
            invite_code=Team.generate_invite_code(),
        )
        db.session.add(team)
        db.session.flush()

        membership = TeamMember(team_id=team.id, user_id=current_user.id, role="admin")
        db.session.add(membership)
        db.session.commit()

        flash(f"Команда успешно создана. Код приглашения: {team.invite_code}", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("projects/create_team.html", form=form)


@bp.route("/teams/join", methods=["GET", "POST"])
@login_required
def join_team():
    form = JoinTeamForm()
    if form.validate_on_submit():
        code = form.invite_code.data.strip().upper()
        team = Team.query.filter_by(invite_code=code).first()

        if team is None:
            flash("Команда с таким кодом не найдена.", "danger")
            return redirect(url_for("projects.join_team"))

        existing = TeamMember.query.filter_by(
            team_id=team.id, user_id=current_user.id
        ).first()
        if existing:
            flash(f"Вы уже состоите в команде «{team.name}».", "info")
            return redirect(url_for("main.dashboard"))

        membership = TeamMember(team_id=team.id, user_id=current_user.id, role="member")
        db.session.add(membership)
        db.session.commit()

        flash(f"Вы вступили в команду «{team.name}».", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("projects/join_team.html", form=form)


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create_project():
    teams = TeamMember.query.filter_by(user_id=current_user.id).all()
    form = ProjectForm()
    form.team_id.choices = [(membership.team.id, membership.team.name) for membership in teams]

    if not form.team_id.choices:
        flash("Сначала создайте команду, а затем проект.", "warning")
        return redirect(url_for("projects.create_team"))

    if form.validate_on_submit():
        membership = TeamMember.query.filter_by(
            team_id=form.team_id.data,
            user_id=current_user.id,
        ).first()
        if membership is None:
            flash("У вас нет доступа к этой команде.", "danger")
            return redirect(url_for("main.dashboard"))

        project = Project(
            team_id=form.team_id.data,
            name=form.name.data,
            description=form.description.data,
        )
        db.session.add(project)
        db.session.commit()

        flash("Проект успешно создан.", "success")
        return redirect(url_for("tasks.project_tasks", project_id=project.id))

    return render_template("projects/create_project.html", form=form)
