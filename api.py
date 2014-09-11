"""HTTP+JSON API for script server."""

import json

from flask import g, request, send_file, session
from flask.ext import restful
from flask.ext.restful import abort

from sessions import start_session, end_session, login_required
import files
import users


class Info(restful.Resource):
    def get(self):
        username = None
        user_id = session.get('user_id')
        if user_id is not None:
            (user_id, username, admin, directory) = users.user_info(user_id)
        running = g.job_manager.count_jobs(g.db, 'running')
        waiting = g.job_manager.count_jobs(g.db, 'waiting')
        return {'version': g.version,
                'name': g.config.get('NAME'),
                'username': username,
                'jobs_running': running,
                'jobs_waiting': waiting}


class Login(restful.Resource):
    def post(self):
        o = json.load(request.stream)
        if not (isinstance(o, dict) and 'username' in o and 'password' in o):
            abort(400)
        username = o['username']
        password = o['password']
        try:
            user_id = users.login(username, password)
        except users.LoginError as e:
            abort(403, message=e.value)
        start_session(user_id)
        return '', 204


class Logout(restful.Resource):
    def post(self):
        end_session()
        return '', 204


class Run(restful.Resource):
    @login_required
    def post(self):
        script = request.data
        job_id = g.job_manager.new_job(g.db, g.user_id, script)
        return {'job_id': job_id}


class Jobs(restful.Resource):
    @login_required
    def get(self):
        return g.job_manager.list_jobs(g.db)


class Job(restful.Resource):

    @login_required
    def get(self, job_id):
        info = g.job_manager.get_job(g.db, job_id)
        if info is None:
            abort(404, message=('No such job: %d' % job_id))
        return info

    @login_required
    def post(self, job_id):

        # check permissions
        if not g.admin:
            owner = g.job_manager.get_job_owner(g.db, job_id)
            if not owner == g.user_id:
                abort(403)

        # carry out request
        o = json.load(request.stream)
        if not (isinstance(o, dict) and 'command' in o):
            abort(400)
        cmd = o['command']
        if cmd == 'terminate':
            try:
                g.job_manager.terminateJob(g.db, job_id)
            except KeyError:
                abort(400, message=('Job %d is not running.' % job_id))
            return '', 204
        elif cmd == 'kill':
            try:
                g.job_manager.killJob(g.db, job_id)
            except KeyError:
                abort(400, message=('Job %d is not running.' % job_id))
            return '', 204
        abort(400, message=('No such command: "%s"' % cmd))


def format_file_info(f):
    info = {}
    info['name'] = f['name']
    info['mtime'] = f['mtime'].isoformat()
    if 'size' in f:
        info['size'] = f['size']
    return info


class File(restful.Resource):

    @login_required
    def get(self, p):
        if not files.exists(p):
            abort(404, message=('File not found: %s' % p))
        if files.is_directory(p):
            return [format_file_info(f) for f in files.directory_listing(p)]
        else:
            return send_file(files.absolute(p))

    @login_required
    def post(self, p):
        if not files.exists(p):
            abort(404, message=('File not found: %s' % p))
        o = json.load(request.stream)
        if not (isinstance(o, dict) and 'command' in o):
            abort(400)
        cmd = o['command']
        try:
            if cmd == 'move':
                if not 'to' in o:
                    abort(400)
                files.move_file(p, o['to'])
            elif cmd == 'copy':
                if not 'to' in o:
                    abort(400)
                files.copy_file(p, o['to'])
            elif cmd == 'mkdir':
                name = o['name']
                if '/' in name:
                    abort(400, message='Invalid filename.')
                if not files.is_directory(p):
                    abort(400, message='Not a directory.')
                if not 'name' in o:
                    abort(400)
                return files.mkdir(p, name)
            else:
                abort(400, message=('Invalid command: %s' % cmd))
        except OSError as e:
            abort(500, message=('File system error: ' + e.strerror))
        except IOError as e:
            abort(500, message=('File system error: ' + e.strerror))
        return '', 204

    @login_required
    def put(self, p):
        block_size = 64 * 1024
        with open(files.absolute(p), 'wb') as f:
            while 1:
                buffer = request.stream.read(block_size)
                if not buffer:
                    break
                f.write(buffer)
        return format_file_info(files.file_info(p))

    @login_required
    def delete(self, p):
        if not files.exists(p):
            abort(404, message=('File not found: %s' % p))
        try:
            files.delete(p)
        except OSError as e:
            abort(501, 'File system error: ' + e.strerror)


def add_api(app):
    """Add JSON API to Flask app."""
    api = restful.Api(app, '/api')
    api.add_resource(Info,   '/info')
    api.add_resource(Login,  '/login')
    api.add_resource(Logout, '/logout')
    api.add_resource(Run,    '/run')
    api.add_resource(Jobs,   '/jobs')
    api.add_resource(Job,    '/jobs/<int:job_id>')
    api.add_resource(File,   '/files/', endpoint='fr', defaults={'p': ''})
    api.add_resource(File,   '/files/<path:p>')
