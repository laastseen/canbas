from flask import current_app, jsonify, render_template, request
from flask_login import current_user

from app.consent import log_consent
from app.extensions import db
from app.legal import bp


@bp.route("/privacy")
def privacy():
    return render_template("legal/privacy.html")


@bp.route("/cookies")
def cookies():
    return render_template("legal/cookies.html")


@bp.route("/api/cookie-consent", methods=["POST"])
def cookie_consent():
    data = request.get_json(silent=True) or {}
    choice = data.get("choice", "necessary")
    if choice not in ("necessary", "all"):
        choice = "necessary"

    consent_type = "cookies_all" if choice == "all" else "cookies_necessary"
    log_consent(
        consent_type,
        email=current_user.email if current_user.is_authenticated else None,
        user_id=current_user.id if current_user.is_authenticated else None,
        policy_version=current_app.config["POLICY_VERSION"],
    )
    db.session.commit()
    return jsonify({"ok": True})
