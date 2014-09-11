from contextlib import closing

from flask import g
from twisted.internet import reactor
from twisted.internet.error import ProcessDone
from twisted.internet.protocol import ProcessProtocol


class RunScriptProtocol(ProcessProtocol):

    """Protocol to handle a running script process."""

    def __init__(self, job_id, script, callback):
        self.job_id = job_id
        self.script = script
        self.callback = callback
        self.out = ''
        self.err = ''

    def connectionMade(self):
        self.transport.write(self.script)
        self.transport.closeStdin()
        del self.script

    def outReceived(self, data):
        self.out += data

    def errReceived(self, data):
        self.err += data

    def processEnded(self, status):
        success = status.type == ProcessDone
        self.callback(success, self.out, self.err)

    def terminate(self):
        self.transport.signalProcess('TERM')

    def kill(self):
        self.transport.signalProcess('KILL')


def spawn(job_id, cmd, args, script, path, callback):
    """Spawn a new script process and return a RunScriptProtocol object."""
    protocol = RunScriptProtocol(job_id, script, callback)
    reactor.spawnProcess(protocol, cmd, [cmd] + args, path=path)
    return protocol
