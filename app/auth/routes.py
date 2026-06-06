from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.admin.services import get_setting
from app.auth import bp
from app.auth.forms import LoginForm, ProfileForm, RegistrationForm
from app.extensions import db
from app.models import User


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if get_setting("registration_enabled", "true") != "true":
        flash("Регистрация временно закрыта.", "warning")
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        email = form.email.data.lower()
        domain = email.split("@")[-1]
        blocked = {d.strip().lower() for d in get_setting("blocked_email_domains", "").split(",") if d.strip()}
        if domain in blocked:
            flash("Регистрация с этого домена email запрещена.", "danger")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter(
            (User.email == form.email.data.lower()) | (User.username == form.username.data)
        ).first()
        if existing_user:
            flash("Пользователь с такой почтой или именем уже существует.", "danger")
            return redirect(url_for("auth.register"))

        user = User(username=form.username.data, email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Аккаунт успешно создан.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Неверная почта или пароль.", "danger")
            return redirect(url_for("auth.login"))
        if not user.is_active:
            flash("Аккаунт заблокирован.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        flash("С возвращением.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # check username/email uniqueness
        conflict = User.query.filter(
            User.id != current_user.id,
            (User.email == form.email.data.lower()) | (User.username == form.username.data),
        ).first()
        if conflict:
            flash("Имя пользователя или почта уже заняты.", "danger")
            return redirect(url_for("auth.profile"))

        current_user.username = form.username.data
        current_user.email = form.email.data.lower()

        if form.new_password.data:
            if not form.current_password.data or not current_user.check_password(form.current_password.data):
                flash("Неверный текущий пароль.", "danger")
                return redirect(url_for("auth.profile"))
            current_user.set_password(form.new_password.data)

        db.session.commit()
        flash("Профиль обновлён.", "success")
        return redirect(url_for("auth.profile"))

    total_tasks = len(current_user.assigned_tasks)
    done_tasks = sum(1 for t in current_user.assigned_tasks if t.status == "done")
    return render_template("auth/profile.html", form=form, total_tasks=total_tasks, done_tasks=done_tasks)
