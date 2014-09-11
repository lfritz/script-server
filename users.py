"""Functions to access the user table in the database."""

from flask import g


class LoginError(Exception):

    """Exception raised if login fails."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def login(username, pwd):
    """Log in.

    If successful, returns user_id. If not, raises LoginError."""
    c = g.db.cursor()
    c.execute('''SELECT user_id, password FROM user WHERE username=?''',
              (username,))
    row = c.fetchone()
    if row is None:
        raise LoginError('User not found: %s' % username)
    (user_id, pw_hash) = row
    if not g.bcrypt.check_password_hash(pw_hash, pwd):
        raise LoginError('Password incorrect')
    return user_id


def user_info(user_id):
    """Get (user_id, username, admin, directory) tuple for a user."""
    c = g.db.cursor()
    c.execute("""SELECT user_id, username, admin, directory
                 FROM user
                 WHERE user_id=?""",
              (user_id,))
    return c.fetchone()


def users():
    """Get a list of users as (user_id, username, directory) tuples."""
    c = g.db.cursor()
    c.execute("SELECT user_id, username, directory FROM user")
    return c.fetchall()


def add_user(username, password, directory):
    """Add a user to the database."""
    password_hash = g.bcrypt.generate_password_hash(password)
    c = g.db.cursor()
    c.execute("""INSERT INTO user (username, password, directory)
                 VALUES (?, ?, ?)""",
              (username, password_hash, directory))
    g.db.commit()


def delete_user(user_id):
    """Delete a user from the database."""
    c = g.db.cursor()
    c.execute("DELETE FROM clipboard WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM user WHERE user_id=?", (user_id,))
    g.db.commit()


def update(user_id, username, directory):
    """Update username and directory for the user with the given user_id."""
    c = g.db.cursor()
    c.execute("UPDATE user SET username=?,directory=? WHERE user_id=?",
              (username, directory, user_id))
    g.db.commit()


def update_password(user_id, pwd):
    """Change the password for a user."""
    password_hash = g.bcrypt.generate_password_hash(password)
    c = g.db.cursor()
    c.execute("UPDATE user SET password=? WHERE user_id=?",
              (password_hash, user_id))
    g.db.commit()


def set_clipboard(user_id, fs):
    """Set the user's clipboard to contain the given list of files."""
    c = g.db.cursor()
    c.execute("DELETE FROM clipboard WHERE user_id=?", (user_id,))
    for f in fs:
        c.execute("INSERT INTO clipboard (user_id, file) values (?, ?)",
                  (user_id, f))
    g.db.commit()


def get_clipboard(user_id):
    """Get a list of the files in the user's clipboard."""
    c = g.db.cursor()
    c.execute("SELECT file FROM clipboard WHERE user_id=?", (user_id,))
    return [row[0] for row in c.fetchall()]


def clear_clipboard(user_id):
    """Remove any entries in the user's clipboard."""
    c = g.db.cursor()
    c.execute("DELETE FROM clipboard WHERE user_id=?", (user_id,))
    g.db.commit()
