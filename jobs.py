from contextlib import closing
from datetime import datetime

import database
import process


def make_callback(job_manager, dbname, job_id):
    def callback(success, out, err):
        with closing(database.connect(dbname)) as db:
            job_manager.process_terminated(db, job_id, success, out, err)
    return callback


class JobManager:

    """A job manager keeps a database of jobs and takes care of starting and
    supervising running jobs."""

    def __init__(self, cmd, args, dbname, max_running):
        self.cmd = cmd
        self.args = args
        self.dbname = dbname
        self.max_running = max_running
        self.running = {}
        with closing(database.connect(dbname)) as db:
            # clean up the database after the server was restarted
            c = db.cursor()
            c.execute("UPDATE job SET status='failed' WHERE status='running'")
            db.commit()
            self._check_queue(db)

    def new_job(self, db, user_id, script):
        """Add a new job and return the job id."""
        c = db.cursor()
        c.execute("INSERT INTO job (user_id, script) VALUES (?, ?)",
                  (user_id, buffer(script)))
        job_id = c.lastrowid
        db.commit()
        self._check_queue(db)
        return job_id

    def list_jobs(self, db):
        """Get a list of all jobs in the database."""
        c = db.cursor()
        result = c.execute("""SELECT job_id, username, status
                              FROM job NATURAL JOIN user
                              ORDER BY job_id""")
        return [{'job_id': row[0], 'user': row[1], 'status': row[2]}
                for row in result]

    def is_job(self, db, job_id):
        """Check if there is a job with the given id in the database."""
        c = db.cursor()
        c.execute("SELECT COUNT(job_id) FROM job WHERE job_id=?", (job_id,))
        row = c.fetchone()
        return row[0]

    def get_job(self, db, job_id):
        """Get information on a job in the database."""
        c = db.cursor()
        c.execute("""SELECT job_id, username, status, script,
                            start_time as "start [timestamp]",
                            end_time as "end [timestamp]",
                            out, err
                     FROM job NATURAL JOIN user
                     WHERE job_id = ?""",
                  (job_id,))
        row = c.fetchone()
        if row is None:
            return None
        (job_id, user, status, script, start, end, out, err) = row
        return {'job_id': job_id,
                'user': user,
                'status': status,
                'script': str(script),
                'start': None if start is None else start.isoformat(),
                'end': None if end is None else end.isoformat(),
                'out': out,
                'err': err}

    def get_job_owner(self, db, job_id):
        """Get the job's owner's user_id."""
        c = db.cursor()
        c.execute("SELECT user_id FROM job WHERE job_id = ?", (job_id,))
        row = c.fetchone()
        return row[0]

    def count_jobs(self, db, status):
        """Count the number of jobs with the given status."""
        c = db.cursor()
        c.execute("SELECT COUNT(job_id) FROM job WHERE status = ?", (status,))
        row = c.fetchone()
        return row[0]

    def terminateJob(self, db, job_id):
        """Ask the job to terminate."""
        self.running[job_id].terminate()

    def killJob(self, db, job_id):
        """Kill the job."""
        self.running[job_id].kill()

    def process_terminated(self, db, job_id, success, out, err):
        """Called after a job terminates."""
        del self.running[job_id]
        c = db.cursor()
        status = 'done' if success else 'failed'
        c.execute("""UPDATE job
                     SET status=?, end_time=datetime('now'), out=?, err=?
                     WHERE job_id=?""",
                  (status, out, err, job_id))
        db.commit()
        self._check_queue(db)

    def _check_queue(self, db):
        """Look up waiting jobs and start as many as possible."""
        if (self.max_running is not None) and \
           (len(self.running) >= self.max_running):
            return
        c = db.cursor()
        c.execute("""SELECT job_id, script, directory
                     FROM job NATURAL JOIN user
                     WHERE status='waiting'
                     ORDER BY job_id LIMIT 1""")
        row = c.fetchone()
        if row is None:
            return
        job_id, script, path = row[0], str(row[1]), row[2]
        cmd = self.cmd
        args = self.args
        callback = make_callback(self, self.dbname, job_id)
        self.running[job_id] = \
            process.spawn(job_id, cmd, args, script, path, callback)
        c.execute("""UPDATE job
                     SET status='running', start_time=datetime('now')
                     WHERE job_id=?""",
                  (job_id,))
        db.commit()
        self._check_queue(db)
