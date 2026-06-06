from functools import wraps

from flask import abort
from flask_login import current_user


def superadmin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superadmin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
