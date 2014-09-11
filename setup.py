#!/usr/bin/env python

"""Create initial database and configuration file for script server."""

from bcrypt import hashpw, gensalt
from contextlib import closing
from getpass import getpass
import os
import socket

import database

print('Script server setup')
hostname = socket.gethostname()
servername = raw_input('Server name: [%s] ' % hostname) or hostname
dbfile = raw_input('Database file: [script-server.db] ') or 'script-server.db'
logfile = raw_input('Log file: [script-server.log] ') or 'script-server.log'

if os.path.exists(dbfile):
    y = raw_input('Database file %s exists already. Overwrite? ' % dbfile)
    if not y.startswith('y'):
        exit(1)
if os.path.exists('script-server.cfg'):
    y = raw_input('Configuration file server.cfg exists already. Overwrite? ')
    if not y.startswith('y'):
        exit(1)

print('Administrator account:')
admin_username = raw_input('Username: [admin] ') or 'admin'
admin_password = getpass('Password: ')

print('Creating initial database...')
hashed_password = hashpw(admin_password, gensalt())
with closing(database.connect(dbfile)) as db:
    with open('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    c = db.cursor()
    c.execute("""INSERT INTO user (username, password, admin, directory)
                 VALUES (?,?,1,'/tmp')""",
              (admin_username, hashed_password))
    db.commit()

print('Creating script-server.cfg file...')
with open('script-server.cfg', 'w') as f:
    f.write("NAME = %s\n" % repr(servername))
    f.write("DATABASE = %s\n" % repr(dbfile))
    f.write("LOGFILE = %s\n" % repr(logfile))
    f.write("SECRET_KEY = %s\n" % repr(os.urandom(24)))
    f.write("PORT = 5000\n")
    f.write("COMMAND = '/usr/bin/python'\n")
    f.write("ARGS = []\n")
    f.write("MAX_RUNNING = 1\n")

print('All done. Edit script-server.cfg or start the server with')
print('    python script-server.py')
