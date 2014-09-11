"""Web-based user interface for script server."""

from flask import abort, Blueprint, flash, g, render_template, redirect
from flask import request, send_file, session, url_for
from werkzeug import secure_filename

from sessions import admin_required, login_required
import files
import sessions
import users

ui = Blueprint('User Interface', __name__)


@ui.route('/')
def index():
    return redirect(url_for('.info'))


@ui.route('/info')
def info():
    if 'user_id' in session:
        sessions.load_user_info()
    title = 'Server %s' % g.config.get('NAME')
    running = g.job_manager.count_jobs(g.db, 'running')
    waiting = g.job_manager.count_jobs(g.db, 'waiting')
    return render_template('info.html', title=title,
                           version=g.version,
                           jobs_running=running,
                           jobs_waiting=waiting)


@ui.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            user_id = users.login(username, password)
            users.clear_clipboard(user_id)
        except users.LoginError as e:
            return render_template('login.html', error=e.value)
        sessions.start_session(user_id)
        return redirect(url_for('.info'))
    return render_template('login.html')


@ui.route('/logout')
def logout():
    sessions.end_session()
    return redirect(url_for('.login'))


@ui.route('/jobs')
@login_required
def jobs():
    g.title = 'Jobs'
    highlight = request.args.get('highlight', None)
    jobs = g.job_manager.list_jobs(g.db)
    return render_template('jobs.html',
                           title='Jobs', jobs=jobs, highlight=highlight)


def signal_job(job_id, action):
    # check permissions
    if not g.admin:
        owner = g.job_manager.get_job_owner(g.db, job_id)
        if not owner == g.user_id:
            return 'You have to be the job owner or administrator.'

    # carry out request
    if action == 'Terminate':
        try:
            g.job_manager.terminateJob(g.db, job_id)
        except KeyError:
            return 'Cannot terminate job %d. Is it running?' % job_id
    elif action == 'Kill':
        try:
            g.job_manager.killJob(g.db, job_id)
        except KeyError:
            return 'Cannot kill job %d. Is it running?' % job_id

    return None


@ui.route('/jobs/<int:job_id>', methods=['GET', 'POST'])
@login_required
def job_details(job_id):
    error = None
    if request.method == 'POST':
        error = signal_job(job_id, request.form['button'])
    job = g.job_manager.get_job(g.db, job_id)
    title = "Job %d" % job['job_id']
    return render_template('job_details.html',
                           title=title, job=job, error=error)


@ui.route('/script', methods=['GET', 'POST'])
@login_required
def script():
    if request.method == 'POST':
        script = request.form['script']
        job_id = g.job_manager.new_job(g.db, g.user_id, script)
        return redirect(url_for('.jobs', highlight=job_id))
    return render_template('script.html', title='Script')


@ui.route('/files/')
@login_required
def file_root():
    return file_listing('')


@ui.route('/files/<path:p>')
@login_required
def file_ui(p):
    path = '/'+p
    if not files.exists(path):
        abort(404)
    if files.is_directory(path):
        return file_listing(p)
    return send_file(files.absolute(path))


def file_listing(p, error=None):
    path = '/'+p

    # get file listing
    def format_info(f):
        info = {}
        info['name'] = f['name']
        info['mtime'] = f['mtime']
        if p == '':
            info['link_path'] = f['name']
        else:
            info['link_path'] = '%s/%s' % (p, f['name'])
        info['size'] = f['size'] if 'size' in f else None
        return info
    listing = [format_info(f) for f in files.directory_listing(path)]

    # get clipboard info
    clipboard_files = users.get_clipboard(g.user_id)
    paste_count = len(clipboard_files)

    # render html template
    return render_template('file_listing.html',
                           title='Files', p=p, files=listing,
                           paste_count=paste_count,
                           error=error)


@ui.route('/file_action', methods=['POST'])
@login_required
def file_action():
    error = None
    action = request.form['button']
    p = request.form['p']
    fs = [k[5:]
          for k in request.form.iterkeys()
          if k.startswith('file_')]
    if action == 'Delete':
        for f in fs:
            try:
                files.delete('/%s/%s' % (p, f))
            except OSError as e:
                error = 'Error deleting %s: %s' % (f, e.strerror)
                break
            except IOError as e:
                error = 'Error deleting %s: %s' % (f, e.strerror)
                break
        return file_listing(p, error)
    elif action in ['Cut', 'Copy']:
        session['clipboard'] = action
        users.set_clipboard(g.user_id, ['/%s/%s' % (p, f) for f in fs])
        return file_listing(p, None)


@ui.route('/file_paste', methods=['POST'])
@login_required
def file_paste():
    p = request.form['p']
    path = '/'+p
    action = session['clipboard']
    fs = users.get_clipboard(g.user_id)
    if action == 'Cut':
        for f in fs:
            files.move_file(f, path)
    else:
        for f in fs:
            files.copy_file(f, path)
    return redirect(url_for('.file_ui', p=p))


@ui.route('/mkdir', methods=['POST'])
@login_required
def mkdir():
    error = None
    p = request.form['p']
    dirname = request.form['dirname']
    path = '/'+p
    files.mkdir(path, dirname)
    return redirect(url_for('.file_ui', p=p))


@ui.route('/upload', methods=['POST'])
@login_required
def upload():
    error = None
    p = request.form['p']
    f = request.files['file']
    if f:
        filename = secure_filename(f.filename)
        f.save(files.absolute('/%s/%s' % (p, filename)))
    return redirect(url_for('.file_ui', p=p))


@ui.route('/users')
@admin_required
def list_users():
    u = [{'user_id': user_id, 'username': username, 'directory': directory}
         for (user_id, username, directory) in users.users()]
    return render_template('list_users.html',
                           title='Users', users=u)


@ui.route('/new_user', methods=['GET', 'POST'])
@admin_required
def new_user():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        users.add_user(username,
                       request.form['password'],
                       request.form['directory'])
        flash('Created user %s.' % username)
        return redirect(url_for('.list_users'))
    return render_template('new_user.html', title='New User', error=error)


@ui.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    if request.method == 'POST':
        action = request.form['button']
        if action == 'Delete':
            users.delete_user(user_id)
        else:
            username = request.form['username']
            directory = request.form['directory']
            users.update(user_id, username, directory)
        return redirect(url_for('.list_users'))
    (user_id, username, admin, directory) = users.user_info(user_id)
    return render_template('edit_user.html',
                           title='User %s' % username,
                           user_id=user_id, username=username,
                           admin=admin, directory=directory)


@ui.route('/change_pwd/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def change_pwd(user_id):
    error = None
    if request.method == 'POST':
        password1 = request.form['password1']
        password2 = request.form['password2']
        if password1 != password2:
            error = "Passwords don't match!"
        else:
            users.update_password(user_id, password1)
            return redirect(url_for('.list_users'))
    u = users.user_info(user_id)
    return render_template('admin_change_pwd.html',
                           title="Change Password for %s" % u['username'],
                           user=u,
                           error=error)
