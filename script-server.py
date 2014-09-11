#!/usr/bin/env python

"""Script server. Run setup.py first to create database and config file."""

import datetime
import logging
import os

from flask import Flask, g
from flask.ext.bcrypt import Bcrypt
from twisted.internet import reactor
from twisted.web.wsgi import WSGIResource
from twisted.python.log import PythonLoggingObserver
from twisted.web.server import Site

import api
import database
import jobs
from ui import ui

version = '0.1.0'

# default settings
NAME = 'localhost'
DATABASE = 'script-server.db'
LOGFILE = 'script-server.log'
SECRET_KEY = os.urandom(24)
PORT = 5000
COMMAND = '/usr/bin/python'
ARGS = []
MAX_RUNNING = 1

# create Flask app
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config.from_object(__name__)
app.config.from_pyfile('script-server.cfg', silent=True)
api.add_api(app)
app.register_blueprint(ui)

# set up JobManager object
job_manager = jobs.JobManager(app.config['COMMAND'],
                              app.config['ARGS'],
                              app.config['DATABASE'],
                              app.config['MAX_RUNNING'])


# before each request: set up 'g', open database connection
@app.before_request
def before_request():
    g.config = app.config
    g.version = version
    g.job_manager = job_manager
    g.db = database.connect(app.config['DATABASE'])
    g.bcrypt = bcrypt


# after each request: close database connection
@app.teardown_request
def teardown_request(exception):
    db = g.get('db')
    if db is not None:
        db.close()


@app.template_filter('format_datetime')
def format_datetime(dt):
    """Format a datetime object in a nice, readable way."""
    time = dt.time().strftime('%H:%M')
    date = dt.date()
    today = datetime.date.today()
    if date == today:
        return "Today " + time
    yesterday = today - datetime.timedelta(days=1)
    if date == yesterday:
        return "Yesterday " + time
    return date.strftime("%Y-%m-%d ") + time


@app.template_filter('format_bytes')
def format_bytes(b):
    """Format filesize in a nice, readable way."""
    if b is None:
        return ''
    prefixes = 'KMGTPEZY'
    n = b
    if n > 1024:
        for prefix in prefixes:
            n /= 1024
            if n < 1024:
                return '%.1f %sB' % (n, prefix)
    return '%d B' % b


# set up logging
file_handler = logging.FileHandler(app.config['LOGFILE'])
app.logger.addHandler(file_handler)
logging.getLogger('twisted').addHandler(file_handler)
observer = PythonLoggingObserver()
observer.start()

# start Twisted server
resource = WSGIResource(reactor, reactor.getThreadPool(), app)
site = Site(resource)
reactor.listenTCP(app.config['PORT'], site)
reactor.run()
