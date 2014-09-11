"""Functions for session management."""

from functools import wraps

from flask import abort, g, session

import users


def load_user_info():
    """Load info for the current user and put it in 'g'."""
    user_id = session.get('user_id')
    (user_id, username, admin, directory) = users.user_info(user_id)
    g.user_id = user_id
    g.username = username
    g.admin = admin
    g.directory = directory


def login_required(f):
    """Decorator for view functions that require the user to be logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not 'user_id' in session:
            abort(401)
        load_user_info()
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator for view functions that require administrator rights."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id is None:
            # user is not logged in
            abort(401)
        (user_id, username, admin, directory) = users.user_info(user_id)
        if not admin:
            # user does not have administrator rights
            abort(403)
        g.user_id = user_id
        g.username = username
        g.admin = admin
        g.directory = directory
        return f(*args, **kwargs)
    return decorated


def start_session(user_id):
    session['user_id'] = user_id


def end_session():
    session.clear()
