from flask import request

from app.extensions import db
from app.models import ConsentLog


def client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or ""


def log_consent(consent_type: str, *, email: str | None = None, user_id: int | None = None, policy_version: str):
    entry = ConsentLog(
        user_id=user_id,
        email=email,
        consent_type=consent_type,
        policy_version=policy_version,
        ip_address=client_ip(),
        user_agent=(request.user_agent.string or "")[:500],
    )
    db.session.add(entry)
